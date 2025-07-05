# app.py - Fixed Flask Application
from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import io
import base64
from werkzeug.utils import secure_filename
import os
import sqlite3
import hashlib
from contextlib import contextmanager
import warnings
warnings.filterwarnings('ignore')

# ML Libraries - with error handling for missing packages
try:
    from sklearn.ensemble import RandomForestRegressor, IsolationForest, RandomForestClassifier
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import LabelEncoder, StandardScaler
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_absolute_error, r2_score
    from sklearn.cluster import KMeans
    import pickle
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    print("ML libraries not available. Install scikit-learn for ML features.")

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['DATABASE'] = 'recruitment_data.db'
app.config['MODELS_FOLDER'] = 'models'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['MODELS_FOLDER'], exist_ok=True)

# Color palette for consistency
COLORS = ['#062C3A', '#ABC100', '#5D858B', '#00617E', '#00A4A6', '#97B8BB', 
          '#F4A41D', '#71164C', '#E2EC57', '#75A1D2', '#344893', '#00A78B', '#C8313F']

class RecruitmentML:
    """Machine Learning engine for recruitment analytics"""
    
    def __init__(self):
        self.ttf_model = None
        self.budget_model = None
        self.success_model = None
        self.anomaly_detector = None
        self.encoders = {}
        self.scaler = None
        self.is_trained = False
        
        if ML_AVAILABLE:
            self.scaler = StandardScaler()
    
    def prepare_features(self, df):
        """Prepare features for ML models"""
        if not ML_AVAILABLE:
            return df
            
        # Create a copy to avoid modifying original
        features_df = df.copy()
        
        # Encode categorical variables
        categorical_cols = ['hiring_manager', 'ta_partner', 'sourcing_partner', 
                           'country', 'project', 'role', 'business_line']
        
        for col in categorical_cols:
            if col in features_df.columns:
                if col not in self.encoders:
                    self.encoders[col] = LabelEncoder()
                    # Fit encoder
                    unique_vals = features_df[col].fillna('Unknown').astype(str)
                    self.encoders[col].fit(unique_vals)
                
                # Transform data
                features_df[f'{col}_encoded'] = self.encoders[col].transform(
                    features_df[col].fillna('Unknown').astype(str)
                )
        
        # Create temporal features
        if 'pos_created' in features_df.columns:
            features_df['pos_created_month'] = features_df['pos_created'].dt.month
            features_df['pos_created_quarter'] = features_df['pos_created'].dt.quarter
            features_df['pos_created_year'] = features_df['pos_created'].dt.year
            features_df['pos_created_weekday'] = features_df['pos_created'].dt.weekday
        
        # Create interaction features
        if 'cvs_shared' in features_df.columns and features_df['cvs_shared'].sum() > 0:
            features_df['cvs_per_ta'] = features_df.groupby('ta_partner')['cvs_shared'].transform('mean')
            features_df['cvs_per_role'] = features_df.groupby('role')['cvs_shared'].transform('mean')
        
        # Create historical performance features
        if 'ta_partner' in features_df.columns:
            if 'time_to_fill' in features_df.columns:
                features_df['ta_historical_avg_ttf'] = features_df.groupby('ta_partner')['time_to_fill'].transform('mean')
            if 'cv_to_interview_rate' in features_df.columns:
                features_df['ta_historical_success_rate'] = features_df.groupby('ta_partner')['cv_to_interview_rate'].transform('mean')
        
        return features_df
    
    def train_time_to_fill_model(self, df):
        """Train model to predict time-to-fill"""
        if not ML_AVAILABLE or 'time_to_fill' not in df.columns or df['time_to_fill'].isna().all():
            return False
        
        # Prepare features
        features_df = self.prepare_features(df)
        
        # Select feature columns (encoded categorical + numerical)
        feature_cols = [col for col in features_df.columns if col.endswith('_encoded') or 
                       col in ['cvs_shared', 'pos_created_month', 'pos_created_quarter',
                              'cvs_per_ta', 'cvs_per_role', 'ta_historical_avg_ttf']]
        
        # Remove rows with missing target
        clean_df = features_df.dropna(subset=['time_to_fill'])
        if len(clean_df) < 10:  # Need minimum data
            return False
        
        X = clean_df[feature_cols].fillna(0)
        y = clean_df['time_to_fill']
        
        # Train model
        self.ttf_model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.ttf_model.fit(X, y)
        
        return True
    
    def train_budget_variance_model(self, df):
        """Train model to predict budget variance"""
        if not ML_AVAILABLE or 'budget_variance_pct' not in df.columns or df['budget_variance_pct'].isna().all():
            return False
        
        features_df = self.prepare_features(df)
        
        feature_cols = [col for col in features_df.columns if col.endswith('_encoded') or 
                       col in ['max_budget', 'cvs_shared', 'pos_created_month',
                              'ta_historical_avg_ttf', 'ta_historical_success_rate']]
        
        clean_df = features_df.dropna(subset=['budget_variance_pct'])
        if len(clean_df) < 10:
            return False
        
        X = clean_df[feature_cols].fillna(0)
        y = clean_df['budget_variance_pct']
        
        self.budget_model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.budget_model.fit(X, y)
        
        return True
    
    def train_success_probability_model(self, df):
        """Train model to predict hiring success probability"""
        if not ML_AVAILABLE or 'accepted' not in df.columns:
            return False
        
        features_df = self.prepare_features(df)
        
        # Create binary success target (1 if accepted > 0, 0 otherwise)
        features_df['success'] = (features_df['accepted'] > 0).astype(int)
        
        feature_cols = [col for col in features_df.columns if col.endswith('_encoded') or 
                       col in ['cvs_shared', 'max_budget', 'pos_created_month',
                              'cvs_per_ta', 'ta_historical_success_rate']]
        
        clean_df = features_df.dropna(subset=['success'])
        if len(clean_df) < 10:
            return False
        
        X = clean_df[feature_cols].fillna(0)
        y = clean_df['success']
        
        self.success_model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.success_model.fit(X, y)
        
        return True
    
    def train_anomaly_detection(self, df):
        """Train anomaly detection model"""
        if not ML_AVAILABLE:
            return False
            
        features_df = self.prepare_features(df)
        
        # Select numerical features for anomaly detection
        numerical_cols = ['time_to_fill', 'cvs_shared', 'interviews_1st', 
                         'max_budget', 'budget_variance_pct']
        
        available_cols = [col for col in numerical_cols if col in features_df.columns]
        if len(available_cols) < 2:
            return False
        
        clean_df = features_df[available_cols].fillna(0)
        
        # Scale features
        scaled_features = self.scaler.fit_transform(clean_df)
        
        # Train anomaly detector
        self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
        self.anomaly_detector.fit(scaled_features)
        
        return True
    
    def train_all_models(self, hired_df, pipeline_df=None):
        """Train all ML models"""
        if not ML_AVAILABLE:
            return False
            
        success_flags = []
        
        if hired_df is not None and not hired_df.empty:
            success_flags.append(self.train_time_to_fill_model(hired_df))
            success_flags.append(self.train_budget_variance_model(hired_df))
            success_flags.append(self.train_success_probability_model(hired_df))
            success_flags.append(self.train_anomaly_detection(hired_df))
        
        self.is_trained = any(success_flags)
        
        # Save models
        if self.is_trained:
            self.save_models()
        
        return self.is_trained
    
    def predict_time_to_fill(self, position_data):
        """Predict time-to-fill for a position"""
        if not ML_AVAILABLE or not self.ttf_model:
            return None
        
        try:
            features_df = self.prepare_features(pd.DataFrame([position_data]))
            feature_cols = [col for col in features_df.columns if col.endswith('_encoded') or 
                           col in ['cvs_shared', 'pos_created_month', 'pos_created_quarter',
                                  'cvs_per_ta', 'cvs_per_role', 'ta_historical_avg_ttf']]
            
            X = features_df[feature_cols].fillna(0)
            prediction = self.ttf_model.predict(X)[0]
            
            return max(1, round(prediction))  # Ensure positive prediction
        except:
            return None
    
    def save_models(self):
        """Save trained models to disk"""
        if not ML_AVAILABLE:
            return False
            
        try:
            models_data = {
                'ttf_model': self.ttf_model,
                'budget_model': self.budget_model,
                'success_model': self.success_model,
                'anomaly_detector': self.anomaly_detector,
                'encoders': self.encoders,
                'scaler': self.scaler,
                'is_trained': self.is_trained
            }
            
            with open(os.path.join(app.config['MODELS_FOLDER'], 'recruitment_models.pkl'), 'wb') as f:
                pickle.dump(models_data, f)
            
            return True
        except:
            return False
    
    def load_models(self):
        """Load trained models from disk"""
        if not ML_AVAILABLE:
            return False
            
        try:
            model_path = os.path.join(app.config['MODELS_FOLDER'], 'recruitment_models.pkl')
            if os.path.exists(model_path):
                with open(model_path, 'rb') as f:
                    models_data = pickle.load(f)
                
                self.ttf_model = models_data.get('ttf_model')
                self.budget_model = models_data.get('budget_model')
                self.success_model = models_data.get('success_model')
                self.anomaly_detector = models_data.get('anomaly_detector')
                self.encoders = models_data.get('encoders', {})
                self.scaler = models_data.get('scaler', StandardScaler() if ML_AVAILABLE else None)
                self.is_trained = models_data.get('is_trained', False)
                
                return True
        except:
            pass
        return False

# Initialize ML engine
ml_engine = RecruitmentML()
if ML_AVAILABLE:
    ml_engine.load_models()  # Try to load existing models on startup

# Database connection helper
@contextmanager
def get_db_connection():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row  # Enable column access by name
    try:
        yield conn
    finally:
        conn.close()

def init_database():
    """Initialize the SQLite database with required tables"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Create uploads table to track file uploads
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS uploads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                file_hash TEXT UNIQUE NOT NULL,
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                has_hired_sheet BOOLEAN DEFAULT 0,
                has_final_sheet BOOLEAN DEFAULT 0
            )
        ''')
        
        # Create hired_data table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS hired_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                upload_id INTEGER,
                req_id TEXT,
                position_title TEXT,
                pos_created DATE,
                filled_date DATE,
                hiring_manager TEXT,
                ta_partner TEXT,
                sourcing_partner TEXT,
                country TEXT,
                project TEXT,
                business_line TEXT,
                role TEXT,
                department TEXT,
                location TEXT,
                cvs_shared INTEGER,
                interviews_1st INTEGER,
                interviews_final INTEGER,
                offers INTEGER,
                accepted INTEGER,
                max_budget REAL,
                accepted_salary REAL,
                currency TEXT,
                time_to_fill INTEGER,
                salary_delta REAL,
                budget_variance_pct REAL,
                cv_to_interview_rate REAL,
                interview_to_offer_rate REAL,
                offer_to_accept_rate REAL,
                FOREIGN KEY (upload_id) REFERENCES uploads (id)
            )
        ''')
        
        # Create final_data table (pipeline data)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS final_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                upload_id INTEGER,
                req_id TEXT,
                position_title TEXT,
                pos_created DATE,
                hiring_manager TEXT,
                ta_partner TEXT,
                sourcing_partner TEXT,
                country TEXT,
                project TEXT,
                business_line TEXT,
                role TEXT,
                job_state TEXT,
                department TEXT,
                location TEXT,
                cvs_shared INTEGER,
                interviews_1st INTEGER,
                interviews_final INTEGER,
                offers INTEGER,
                max_budget REAL,
                currency TEXT,
                position_age INTEGER,
                cv_to_interview_rate REAL,
                interview_to_offer_rate REAL,
                FOREIGN KEY (upload_id) REFERENCES uploads (id)
            )
        ''')
        
        conn.commit()

def calculate_file_hash(file_content):
    """Calculate MD5 hash of file content"""
    return hashlib.md5(file_content).hexdigest()

def normalize_column_names(df):
    """Normalize column names by removing extra spaces, special characters, and standardizing format"""
    df = df.copy()
    
    # Create a mapping of original to normalized column names
    normalized_columns = {}
    
    for col in df.columns:
        # Remove leading/trailing spaces
        normalized_col = str(col).strip()
        
        # Replace multiple spaces with single space
        normalized_col = ' '.join(normalized_col.split())
        
        # Convert to title case for consistency
        normalized_col = normalized_col.title()
        
        # Handle common variations and typos
        normalized_col = normalized_col.replace('Ta Partner', 'TA Partner')
        normalized_col = normalized_col.replace('Tapartner', 'TA Partner')
        normalized_col = normalized_col.replace('Ta_Partner', 'TA Partner')
        normalized_col = normalized_col.replace('Cv', 'CV')
        normalized_col = normalized_col.replace('Id', 'ID')
        normalized_col = normalized_col.replace('Req Id', 'Req ID')
        normalized_col = normalized_col.replace('1St', '1st')
        normalized_col = normalized_col.replace('2Nd', '2nd')
        normalized_col = normalized_col.replace('3Rd', '3rd')
        
        normalized_columns[col] = normalized_col
    
    # Rename columns
    df = df.rename(columns=normalized_columns)
    
    return df

def prepare_df(df, sheet_type):
    """Standardize and clean the dataframe based on sheet type"""
    if df is None or df.empty:
        return df
        
    df = df.copy()
    
    # First normalize all column names
    df = normalize_column_names(df)
    
    # Standardize TA Partner column variations
    ta_partner_variations = ['TA Partner', 'TAPartner', 'Ta Partner', 'Tapartner', 'Ta_Partner']
    for variation in ta_partner_variations:
        if variation in df.columns:
            df['TA Partner'] = df[variation]
            if variation != 'TA Partner':
                df = df.drop(columns=[variation])
            break
    
    if 'TA Partner' not in df.columns:
        df['TA Partner'] = 'Unknown'
    
    # Handle Sourcing Partner column variations
    sourcing_partner_variations = ['Sourcing Partner', 'SourcingPartner', 'Sourcing_Partner', 'Source Partner']
    for variation in sourcing_partner_variations:
        if variation in df.columns:
            df['Sourcing Partner'] = df[variation]
            if variation != 'Sourcing Partner':
                df = df.drop(columns=[variation])
            break
    
    if 'Sourcing Partner' not in df.columns:
        df['Sourcing Partner'] = 'Unknown'
    
    # Column mapping for standardization (using normalized names)
    column_mapping = {
        'Position Created Date': 'pos_created',
        'Hiring Manager': 'hiring_manager',
        'Country': 'country',
        'Project': 'project',
        'Business Line': 'business_line',
        'Role': 'role',
        'Job State': 'job_state',
        'Number Of CVs Shared': 'cvs_shared',
        'Number Of 1st Interviews': 'interviews_1st',
        'Number Of Final Interviews': 'interviews_final',
        'Number Of Offers': 'offers',
        'Number Of Accepted Offers': 'accepted',
        'Max Budgeted Salary': 'max_budget',
        'Currency': 'currency',
        'TA Partner': 'ta_partner',
        'Sourcing Partner': 'sourcing_partner',
        'Req ID': 'req_id',
        'Position Title': 'position_title',
        'Department': 'department',
        'Location': 'location'
    }
    
    # Add sheet-specific mappings
    if sheet_type == 'hired':
        column_mapping.update({
            'Filled Date': 'filled_date',
            'Accepted Salary': 'accepted_salary',
            'Offer Date': 'offer_date',
            'Start Date': 'start_date'
        })
    
    # Rename columns that exist
    for old_name, new_name in column_mapping.items():
        if old_name in df.columns:
            df = df.rename(columns={old_name: new_name})
    
    # Convert date columns with error handling
    date_columns = ['pos_created']
    if sheet_type == 'hired':
        date_columns.extend(['filled_date', 'offer_date', 'start_date'])
    
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    
    # Calculate derived metrics for hired data
    if sheet_type == 'hired':
        if 'filled_date' in df.columns and 'pos_created' in df.columns:
            df['time_to_fill'] = (df['filled_date'] - df['pos_created']).dt.days
        
        if 'accepted_salary' in df.columns and 'max_budget' in df.columns:
            df['salary_delta'] = pd.to_numeric(df['accepted_salary'], errors='coerce') - pd.to_numeric(df['max_budget'], errors='coerce')
            df['budget_variance_pct'] = ((pd.to_numeric(df['accepted_salary'], errors='coerce') - pd.to_numeric(df['max_budget'], errors='coerce')) / pd.to_numeric(df['max_budget'], errors='coerce') * 100)
    
    # Calculate position age for active positions
    if sheet_type == 'final':
        if 'pos_created' in df.columns:
            df['position_age'] = (datetime.now() - df['pos_created']).dt.days
    
    # Calculate conversion rates with proper error handling
    numeric_cols = ['cvs_shared', 'interviews_1st', 'interviews_final', 'offers', 'accepted']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    if all(col in df.columns for col in ['cvs_shared', 'interviews_1st']):
        df['cv_to_interview_rate'] = np.where(df['cvs_shared'] > 0, 
                                            df['interviews_1st'] / df['cvs_shared'] * 100, 0)
    
    if all(col in df.columns for col in ['interviews_1st', 'offers']):
        df['interview_to_offer_rate'] = np.where(df['interviews_1st'] > 0, 
                                               df['offers'] / df['interviews_1st'] * 100, 0)
    
    if all(col in df.columns for col in ['offers', 'accepted']):
        df['offer_to_accept_rate'] = np.where(df['offers'] > 0, 
                                            df['accepted'] / df['offers'] * 100, 0)
    
    # Fill missing values for categorical columns
    categorical_cols = ['hiring_manager', 'country', 'project', 'business_line', 'role', 
                       'job_state', 'ta_partner', 'sourcing_partner', 'currency', 'department', 'location']
    for col in categorical_cols:
        if col in df.columns:
            df[col] = df[col].fillna('Unknown')
    
    return df

# Initialize database on startup
init_database()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and file.filename.endswith(('.xlsx', '.xls')):
        try:
            # Read file content for hash calculation
            file_content = file.read()
            file_hash = calculate_file_hash(file_content)
            
            # Check if file already exists
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT id FROM uploads WHERE file_hash = ?', (file_hash,))
                existing = cursor.fetchone()
                
                if existing:
                    return jsonify({
                        'success': True,
                        'message': f'File already exists in database. Loading existing data.',
                        'has_hired': True,
                        'has_final': True,
                        'upload_id': existing['id']
                    })
            
            # Reset file pointer after reading for hash
            file.seek(0)
            
            # Read Excel file
            excel_file = pd.ExcelFile(file)
            
            hired_data = None
            final_data = None
            has_hired = False
            has_final = False
            
            # Process sheets
            if 'Hired' in excel_file.sheet_names:
                hired_df = pd.read_excel(file, sheet_name='Hired')
                hired_data = prepare_df(hired_df, 'hired')
                has_hired = True
            
            if 'Final' in excel_file.sheet_names:
                final_df = pd.read_excel(file, sheet_name='Final')
                final_data = prepare_df(final_df, 'final')
                has_final = True
            
            if not has_hired and not has_final:
                return jsonify({'error': 'No "Hired" or "Final" sheets found in the Excel file'}), 400
            
            # Save upload record to database
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO uploads (filename, file_hash, has_hired_sheet, has_final_sheet)
                    VALUES (?, ?, ?, ?)
                ''', (secure_filename(file.filename), file_hash, has_hired, has_final))
                upload_id = cursor.lastrowid
                conn.commit()
            
            # Save data to database
            if hired_data is not None:
                save_to_database(hired_data, 'hired', upload_id)
            
            if final_data is not None:
                save_to_database(final_data, 'final', upload_id)
            
            # Train ML models with new data
            try:
                if ML_AVAILABLE:
                    retrain_ml_models()
            except Exception as e:
                print(f"ML training error: {e}")  # Log but don't fail upload
            
            return jsonify({
                'success': True,
                'message': f'Successfully processed and saved {file.filename}',
                'has_hired': has_hired,
                'has_final': has_final,
                'upload_id': upload_id,
                'ml_trained': ml_engine.is_trained if ML_AVAILABLE else False
            })
            
        except Exception as e:
            return jsonify({'error': f'Error processing file: {str(e)}'}), 500
    
    return jsonify({'error': 'Invalid file format. Please upload an Excel file (.xlsx or .xls)'}), 400

def save_to_database(df, sheet_type, upload_id):
    """Save processed dataframe to SQLite database"""
    if df is None or df.empty:
        return
        
    with get_db_connection() as conn:
        # Prepare data for database insertion
        df_clean = df.copy()
        
        # Add upload_id
        df_clean['upload_id'] = upload_id
        
        # Convert datetime columns to string for SQLite
        for col in df_clean.columns:
            if df_clean[col].dtype == 'datetime64[ns]':
                df_clean[col] = df_clean[col].dt.strftime('%Y-%m-%d').replace('NaT', None)
        
        # Replace NaN with None for SQLite
        df_clean = df_clean.where(pd.notnull(df_clean), None)
        
        # Determine table name
        table_name = 'hired_data' if sheet_type == 'hired' else 'final_data'
        
        # Clear existing data for this upload_id
        cursor = conn.cursor()
        cursor.execute(f'DELETE FROM {table_name} WHERE upload_id = ?', (upload_id,))
        
        # Insert new data
        df_clean.to_sql(table_name, conn, if_exists='append', index=False)
        conn.commit()

def load_from_database(sheet_type, upload_id=None):
    """Load data from SQLite database"""
    with get_db_connection() as conn:
        table_name = 'hired_data' if sheet_type == 'hired' else 'final_data'
        
        if upload_id:
            query = f'SELECT * FROM {table_name} WHERE upload_id = ?'
            df = pd.read_sql_query(query, conn, params=(upload_id,))
        else:
            # Get most recent upload
            query = f'''
                SELECT d.* FROM {table_name} d
                JOIN uploads u ON d.upload_id = u.id
                WHERE u.id = (SELECT MAX(id) FROM uploads)
            '''
            df = pd.read_sql_query(query, conn)
        
        if df.empty:
            return None
            
        # Convert date strings back to datetime
        date_columns = ['pos_created']
        if sheet_type == 'hired':
            date_columns.extend(['filled_date', 'offer_date', 'start_date'])
        
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        return df

def retrain_ml_models():
    """Retrain ML models with all available data"""
    if not ML_AVAILABLE:
        return False
        
    try:
        # Load all hired data for training
        hired_df = load_from_database('hired')
        pipeline_df = load_from_database('final')
        
        if hired_df is not None and len(hired_df) >= 10:  # Need minimum data for training
            success = ml_engine.train_all_models(hired_df, pipeline_df)
            print(f"ML models retrained: {success}")
            return success
        else:
            print("Insufficient data for ML training")
            return False
    
    except Exception as e:
        print(f"ML retraining error: {e}")
        return False

@app.route('/api/filter-options/<dashboard_type>')
def get_filter_options(dashboard_type):
    upload_id = request.args.get('upload_id')
    
    # Load data from database
    df = load_from_database('hired' if dashboard_type == 'hired' else 'final', upload_id)
    
    if df is None or df.empty:
        return jsonify({})
    
    options = {}
    
    # Get unique values for filter dropdowns
    filter_columns = ['hiring_manager', 'ta_partner', 'country', 'project']
    for col in filter_columns:
        if col in df.columns:
            unique_values = sorted([str(val) for val in df[col].unique() if pd.notna(val)])
            options[col] = unique_values
    
    # Date range
    if 'pos_created' in df.columns:
        min_date = df['pos_created'].min().strftime('%Y-%m-%d') if pd.notna(df['pos_created'].min()) else None
        max_date = df['pos_created'].max().strftime('%Y-%m-%d') if pd.notna(df['pos_created'].max()) else None
        options['date_range'] = {'min': min_date, 'max': max_date}
    
    return jsonify(options)

@app.route('/api/ml-status')
def get_ml_status():
    """Get ML model training status and capabilities"""
    if not ML_AVAILABLE:
        return jsonify({
            'is_trained': False,
            'models': {},
            'capabilities': ['ML libraries not installed'],
            'training_requirements': 'Install scikit-learn: pip install scikit-learn'
        })
    
    return jsonify({
        'is_trained': ml_engine.is_trained,
        'models': {
            'time_to_fill': ml_engine.ttf_model is not None,
            'budget_variance': ml_engine.budget_model is not None,
            'success_probability': ml_engine.success_model is not None,
            'anomaly_detection': ml_engine.anomaly_detector is not None
        },
        'capabilities': [
            'Time-to-fill prediction',
            'Budget variance forecasting',
            'Hiring success probability',
            'Anomaly detection',
            'Pattern recognition',
            'Performance recommendations'
        ] if ml_engine.is_trained else ['Waiting for training data'],
        'training_requirements': 'Minimum 10 historical records needed for training'
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)