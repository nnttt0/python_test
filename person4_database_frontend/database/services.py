"""数据库操作服务"""
from sqlalchemy.orm import Session
from database.models import PredictionRecord
from typing import List, Dict, Optional
import uuid
from datetime import datetime


class PredictionService:
    """预测记录服务"""
    
    @staticmethod
    def save_single_prediction(db: Session, input_data: Dict, result: Dict) -> PredictionRecord:
        """保存单次预测记录"""
        record = PredictionRecord(
            gender=input_data.get('gender', ''),
            age=float(input_data.get('age', 0)),
            hypertension=int(input_data.get('hypertension', 0)),
            heart_disease=int(input_data.get('heart_disease', 0)),
            ever_married=input_data.get('ever_married', ''),
            work_type=input_data.get('work_type', ''),
            residence_type=input_data.get('residence_type', ''),
            avg_glucose_level=float(input_data.get('avg_glucose_level', 0)) if input_data.get('avg_glucose_level') else None,
            bmi=float(input_data.get('bmi', 0)) if input_data.get('bmi') else None,
            smoking_status=input_data.get('smoking_status', ''),
            risk_score=result.get('risk', 0),
            risk_percent=result.get('risk_percent', 0),
            risk_level=result.get('level', 'safe'),
            suggestion=result.get('suggestion', ''),
            prediction_type='single'
        )
        
        db.add(record)
        db.commit()
        db.refresh(record)
        return record
    
    @staticmethod
    def save_batch_predictions(db: Session, records: List[Dict], batch_id: str = None) -> List[PredictionRecord]:
        """保存批量预测记录"""
        if not batch_id:
            batch_id = str(uuid.uuid4())[:8]
        
        saved_records = []
        for record_data in records:
            record = PredictionRecord(
                gender=record_data.get('gender', ''),
                age=float(record_data.get('age', 0)),
                hypertension=int(record_data.get('hypertension', 0)),
                heart_disease=int(record_data.get('heart_disease', 0)),
                ever_married=record_data.get('ever_married', ''),
                work_type=record_data.get('work_type', ''),
                residence_type=record_data.get('residence_type', ''),
                avg_glucose_level=float(record_data.get('avg_glucose_level', 0)) if record_data.get('avg_glucose_level') else None,
                bmi=float(record_data.get('bmi', 0)) if record_data.get('bmi') else None,
                smoking_status=record_data.get('smoking_status', ''),
                risk_score=record_data.get('risk_score', 0),
                risk_percent=record_data.get('risk_percent', 0),
                risk_level=record_data.get('risk_level', 'safe'),
                suggestion=record_data.get('suggestion', ''),
                prediction_type='batch',
                batch_id=batch_id
            )
            db.add(record)
            saved_records.append(record)
        
        db.commit()
        for record in saved_records:
            db.refresh(record)
        
        return saved_records
    
    @staticmethod
    def get_prediction_by_id(db: Session, prediction_id: int) -> Optional[PredictionRecord]:
        """根据ID获取预测记录"""
        return db.query(PredictionRecord).filter(PredictionRecord.id == prediction_id).first()
    
    @staticmethod
    def get_predictions_by_batch(db: Session, batch_id: str) -> List[PredictionRecord]:
        """根据批次ID获取预测记录"""
        return db.query(PredictionRecord).filter(PredictionRecord.batch_id == batch_id).all()
    
    @staticmethod
    def get_all_predictions(db: Session, limit: int = 100, offset: int = 0) -> List[PredictionRecord]:
        """获取所有预测记录（分页）"""
        return db.query(PredictionRecord).order_by(PredictionRecord.created_at.desc()).limit(limit).offset(offset).all()
    
    @staticmethod
    def get_statistics(db: Session) -> Dict:
        """获取预测统计数据"""
        total = db.query(PredictionRecord).count()
        high_risk = db.query(PredictionRecord).filter(PredictionRecord.risk_level == 'danger').count()
        medium_risk = db.query(PredictionRecord).filter(PredictionRecord.risk_level == 'warning').count()
        low_risk = db.query(PredictionRecord).filter(PredictionRecord.risk_level == 'safe').count()
        
        return {
            'total': total,
            'high_risk': high_risk,
            'medium_risk': medium_risk,
            'low_risk': low_risk,
            'high_risk_rate': round(high_risk / total * 100, 2) if total > 0 else 0
        }

