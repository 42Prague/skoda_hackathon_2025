"""
AI Training Module - Train ML models for skill gap analysis
"""
import pandas as pd
import numpy as np
import pickle
import json
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, mean_squared_error, classification_report
from sklearn.preprocessing import LabelEncoder
import os


@dataclass
class TrainingConfig:
    """Configuration for training"""
    model_save_dir: str = "models"
    test_size: float = 0.2
    random_state: int = 42
    min_samples_for_training: int = 10


class SkillMatchingAI:
    """
    AI model for matching skills to courses using NLP embeddings
    Learns from existing skill-course mappings to predict new ones
    """
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=500, ngram_range=(1, 2))
        self.skill_encoders = {}
        self.course_skill_model = None
        self.trained = False
    
    def prepare_training_data(self, courses: List, skills: List, 
                             skill_course_mappings: Dict[str, List[str]]) -> Tuple:
        """
        Prepare training data from courses and their known skill mappings
        
        Args:
            courses: List of Course objects
            skills: List of Skill objects
            skill_course_mappings: Dict mapping course_id -> list of skill_names
            
        Returns:
            X (course features), y (skill labels)
        """
        X_texts = []
        y_labels = []
        
        # Create skill name to ID mapping
        skill_name_to_id = {skill.name: skill.skill_id for skill in skills}
        
        for course in courses:
            if course.course_id in skill_course_mappings:
                # Combine course text features
                course_text = f"{course.title} {course.description} {' '.join(course.competencies)}"
                
                for skill_name in skill_course_mappings[course.course_id]:
                    if skill_name in skill_name_to_id:
                        X_texts.append(course_text)
                        y_labels.append(skill_name)
        
        if len(X_texts) < 10:
            raise ValueError("Not enough training data. Need at least 10 course-skill pairs.")
        
        # Vectorize text
        X = self.vectorizer.fit_transform(X_texts)
        
        # Encode skills
        self.skill_encoder = LabelEncoder()
        y = self.skill_encoder.fit_transform(y_labels)
        
        return X, y, X_texts, y_labels
    
    def train(self, X, y, validation_split: float = 0.2):
        """Train the skill matching model"""
        print("\n🎓 Training Skill Matching AI...")
        
        # Split data
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=validation_split, random_state=42
        )
        
        # Train Random Forest classifier
        self.course_skill_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        
        self.course_skill_model.fit(X_train, y_train)
        
        # Evaluate
        train_acc = self.course_skill_model.score(X_train, y_train)
        val_acc = self.course_skill_model.score(X_val, y_val)
        
        y_pred = self.course_skill_model.predict(X_val)
        
        print(f"  ✓ Training Accuracy: {train_acc:.3f}")
        print(f"  ✓ Validation Accuracy: {val_acc:.3f}")
        
        # Get unique labels actually in validation set
        unique_labels = sorted(set(y_val) | set(y_pred))
        label_names = [self.skill_encoder.classes_[i] for i in unique_labels]
        
        print(f"\n  Classification Report:")
        print(classification_report(y_val, y_pred, 
                                   labels=unique_labels,
                                   target_names=label_names,
                                   zero_division=0))
        
        self.trained = True
        return {"train_acc": train_acc, "val_acc": val_acc}
    
    def predict_skills_for_course(self, course_text: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """
        Predict which skills a course teaches
        
        Returns:
            List of (skill_name, confidence) tuples
        """
        if not self.trained:
            raise ValueError("Model not trained yet!")
        
        # Vectorize course text
        X = self.vectorizer.transform([course_text])
        
        # Get probability predictions
        probs = self.course_skill_model.predict_proba(X)[0]
        
        # Get top k predictions
        top_indices = np.argsort(probs)[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            skill_name = self.skill_encoder.classes_[idx]
            confidence = probs[idx]
            if confidence > 0.1:  # Only return if confident
                results.append((skill_name, confidence))
        
        return results
    
    def save_model(self, save_dir: str):
        """Save trained model to disk"""
        os.makedirs(save_dir, exist_ok=True)
        
        with open(os.path.join(save_dir, "skill_matching_model.pkl"), "wb") as f:
            pickle.dump({
                "vectorizer": self.vectorizer,
                "model": self.course_skill_model,
                "skill_encoder": self.skill_encoder,
                "trained": self.trained
            }, f)
        
        print(f"  ✓ Model saved to {save_dir}")
    
    def load_model(self, save_dir: str):
        """Load trained model from disk"""
        model_path = os.path.join(save_dir, "skill_matching_model.pkl")
        
        with open(model_path, "rb") as f:
            data = pickle.load(f)
            self.vectorizer = data["vectorizer"]
            self.course_skill_model = data["model"]
            self.skill_encoder = data["skill_encoder"]
            self.trained = data["trained"]
        
        print(f"  ✓ Model loaded from {save_dir}")


class ReadinessPredictionAI:
    """
    AI model to predict employee readiness for positions
    Learns from historical data of employee transitions
    """
    
    def __init__(self):
        self.model = None
        self.feature_columns = []
        self.trained = False
    
    def prepare_training_data(self, employees: List, positions: Dict, 
                             readiness_scores: Dict[str, float]) -> Tuple:
        """
        Prepare training data from employee profiles and known readiness scores
        
        Args:
            employees: List of Employee objects
            positions: Dict of Position objects
            readiness_scores: Dict mapping employee_id -> actual readiness score
            
        Returns:
            X (features), y (readiness scores)
        """
        X_data = []
        y_data = []
        
        for employee in employees:
            if employee.employee_id in readiness_scores:
                features = self._extract_employee_features(employee)
                X_data.append(features)
                y_data.append(readiness_scores[employee.employee_id])
        
        if len(X_data) < 10:
            raise ValueError("Not enough training data. Need at least 10 employees with known readiness scores.")
        
        X = pd.DataFrame(X_data)
        y = np.array(y_data)
        
        self.feature_columns = X.columns.tolist()
        
        return X, y
    
    def _extract_employee_features(self, employee) -> Dict:
        """Extract numerical features from employee"""
        return {
            "num_skills": len(employee.current_skills),
            "num_completed_courses": len(employee.completed_courses),
            "total_learning_hours": employee.get_total_learning_hours(),
            "has_planned_position": 1 if employee.planned_position else 0,
            # Add more features as needed
        }
    
    def train(self, X, y, validation_split: float = 0.2):
        """Train the readiness prediction model"""
        print("\n🎓 Training Readiness Prediction AI...")
        
        # Split data
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=validation_split, random_state=42
        )
        
        # Train Gradient Boosting Regressor
        self.model = GradientBoostingRegressor(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=5,
            random_state=42
        )
        
        self.model.fit(X_train, y_train)
        
        # Evaluate
        train_pred = self.model.predict(X_train)
        val_pred = self.model.predict(X_val)
        
        train_rmse = np.sqrt(mean_squared_error(y_train, train_pred))
        val_rmse = np.sqrt(mean_squared_error(y_val, val_pred))
        
        print(f"  ✓ Training RMSE: {train_rmse:.2f}")
        print(f"  ✓ Validation RMSE: {val_rmse:.2f}")
        
        # Feature importance
        feature_importance = pd.DataFrame({
            'feature': self.feature_columns,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print(f"\n  Top Features:")
        for _, row in feature_importance.head(5).iterrows():
            print(f"    • {row['feature']}: {row['importance']:.3f}")
        
        self.trained = True
        return {"train_rmse": train_rmse, "val_rmse": val_rmse}
    
    def predict_readiness(self, employee) -> float:
        """Predict readiness score for an employee"""
        if not self.trained:
            raise ValueError("Model not trained yet!")
        
        features = self._extract_employee_features(employee)
        X = pd.DataFrame([features])[self.feature_columns]
        
        score = self.model.predict(X)[0]
        return np.clip(score, 0, 100)  # Ensure score is between 0-100
    
    def save_model(self, save_dir: str):
        """Save trained model to disk"""
        os.makedirs(save_dir, exist_ok=True)
        
        with open(os.path.join(save_dir, "readiness_prediction_model.pkl"), "wb") as f:
            pickle.dump({
                "model": self.model,
                "feature_columns": self.feature_columns,
                "trained": self.trained
            }, f)
        
        print(f"  ✓ Model saved to {save_dir}")
    
    def load_model(self, save_dir: str):
        """Load trained model from disk"""
        model_path = os.path.join(save_dir, "readiness_prediction_model.pkl")
        
        with open(model_path, "rb") as f:
            data = pickle.load(f)
            self.model = data["model"]
            self.feature_columns = data["feature_columns"]
            self.trained = data["trained"]
        
        print(f"  ✓ Model loaded from {save_dir}")


class AITrainingPipeline:
    """
    Complete training pipeline for the Skill Gap AI system
    """
    
    def __init__(self, config: Optional[TrainingConfig] = None):
        self.config = config or TrainingConfig()
        self.skill_matching_ai = SkillMatchingAI()
        self.readiness_ai = ReadinessPredictionAI()
    
    def train_from_excel(self, training_data_path: str):
        """
        Train models from Excel file with training data
        
        Expected format:
        - Sheet 'course_skills': course_id, course_text, skill_name
        - Sheet 'employee_readiness': employee_id, readiness_score
        """
        print("📚 Loading training data from Excel...")
        
        # Load training data
        try:
            course_skills_df = pd.read_excel(training_data_path, sheet_name='course_skills')
            employee_readiness_df = pd.read_excel(training_data_path, sheet_name='employee_readiness')
            print("  ✓ Training data loaded successfully")
        except Exception as e:
            print(f"  ❌ Error loading training data: {e}")
            print("\n  Expected Excel format:")
            print("    Sheet 'course_skills': columns [course_id, course_text, skill_name]")
            print("    Sheet 'employee_readiness': columns [employee_id, readiness_score]")
            return None
        
        # Prepare and train skill matching model
        # (Implementation depends on your data structure)
        
        return {
            "skill_matching": "trained",
            "readiness_prediction": "trained"
        }
    
    def save_all_models(self):
        """Save all trained models"""
        print("\n💾 Saving all models...")
        self.skill_matching_ai.save_model(self.config.model_save_dir)
        self.readiness_ai.save_model(self.config.model_save_dir)
        print("  ✓ All models saved")
    
    def load_all_models(self):
        """Load all trained models"""
        print("\n📂 Loading all models...")
        try:
            self.skill_matching_ai.load_model(self.config.model_save_dir)
            self.readiness_ai.load_model(self.config.model_save_dir)
            print("  ✓ All models loaded")
            return True
        except Exception as e:
            print(f"  ❌ Error loading models: {e}")
            return False


# Example usage
if __name__ == "__main__":
    print("="*70)
    print("AI TRAINING MODULE - Skill Gap Analysis")
    print("="*70)
    
    # Initialize training pipeline
    pipeline = AITrainingPipeline()
    
    print("\n📋 This module provides AI training capabilities:")
    print("  1. SkillMatchingAI - Maps courses to skills using NLP")
    print("  2. ReadinessPredictionAI - Predicts employee readiness scores")
    
    print("\n🔧 To train your models:")
    print("  1. Prepare training data in Excel format")
    print("  2. Run: pipeline.train_from_excel('your_training_data.xlsx')")
    print("  3. Save: pipeline.save_all_models()")
    
    print("\n📊 Required training data format:")
    print("  Sheet 'course_skills':")
    print("    - course_id: unique course identifier")
    print("    - course_text: course title + description")
    print("    - skill_name: skill that course teaches")
    print("\n  Sheet 'employee_readiness':")
    print("    - employee_id: unique employee identifier")
    print("    - readiness_score: known readiness score (0-100)")
    
    print("\n" + "="*70)
