# app/core/storage/models.py
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Index
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from .constants import TranslatorType, OperationType

Base = declarative_base()


class ASRCache(Base):
    """语音识别缓存表"""

    __tablename__ = "asr_cache"

    id = Column(Integer, primary_key=True)
    crc32_hex = Column(String(8), unique=True, nullable=False, index=True)
    asr_type = Column(String(50), nullable=False)  # ASR服务类型
    result_data = Column(JSON, nullable=False)  # ASR结果数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TranslationCache(Base):
    """翻译结果缓存表"""

    __tablename__ = "translation_cache"

    id = Column(Integer, primary_key=True)
    source_text = Column(Text, nullable=False)
    translated_text = Column(Text, nullable=False)
    translator_type = Column(String(50), nullable=False)
    params = Column(JSON)
    content_hash = Column(String(32), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (Index("idx_translation_lookup", content_hash, translator_type),)

    def __repr__(self):
        return f"<Translation(id={self.id}, translator={self.translator_type})>"


class LLMCache(Base):
    """LLM调用结果缓存表"""

    __tablename__ = "llm_cache"

    id = Column(Integer, primary_key=True)
    prompt = Column(Text, nullable=False)
    result = Column(Text, nullable=False)
    model_name = Column(String(100), nullable=False)
    params = Column(JSON)
    content_hash = Column(String(32), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (Index("idx_llm_lookup", content_hash, model_name),)

    def __repr__(self):
        return f"<LlmResult(id={self.id}, model={self.model_name})>"


class UsageStatistics(Base):
    """使用统计表"""

    __tablename__ = "usage_statistics"

    id = Column(Integer, primary_key=True)
    operation_type = Column(String(50), nullable=False)
    service_name = Column(String(50), nullable=False)
    call_count = Column(Integer, default=0)
    token_count = Column(Integer, default=0)
    last_updated = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_usage_lookup", operation_type, service_name, unique=True),
    )

    def __repr__(self):
        return f"<UsageStatistics({self.operation_type}:{self.service_name})>"
