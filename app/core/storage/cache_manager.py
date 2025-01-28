# app/core/storage/cache_manager.py
import hashlib
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from .constants import CACHE_CONFIG, OperationType, TranslatorType
from .database import DatabaseManager
from .models import LLMCache, TranslationCache, UsageStatistics, ASRCache

logger = logging.getLogger(__name__)


class CacheManager:
    """缓存管理器，提供高级缓存操作接口"""

    def __init__(self, app_data_path: str):
        if not app_data_path:
            raise ValueError("app_data_path cannot be empty")
        self.db_manager = DatabaseManager(app_data_path)
        self._setup_logging()

    def _setup_logging(self):
        """设置日志记录"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def _generate_hash(self, content: str, params: Dict[str, Any]) -> str:
        """生成内容和参数的组合哈希值"""
        if not content:
            raise ValueError("Content cannot be empty")
        if params is None:
            params = {}
        combined = f"{content}{json.dumps(params, sort_keys=True)}"
        return hashlib.md5(combined.encode()).hexdigest()

    def _validate_translator_type(self, translator_type: str):
        """验证翻译器类型"""
        valid_types = [t.value for t in TranslatorType]
        if translator_type not in valid_types:
            raise ValueError(f"Invalid translator type. Must be one of: {valid_types}")

    def _validate_operation_type(self, operation_type: str):
        """验证操作类型"""
        valid_types = [t.value for t in OperationType]
        if operation_type not in valid_types:
            raise ValueError(f"Invalid operation type. Must be one of: {valid_types}")

    def cleanup_old_cache(self):
        """清理过期缓存"""
        cleanup_date = datetime.utcnow() - CACHE_CONFIG["max_age"]
        with self.db_manager.get_session() as session:
            # 清理翻译缓存
            session.query(TranslationCache).filter(
                TranslationCache.created_at < cleanup_date
            ).delete()
            # 清理LLM结果缓存
            session.query(LLMCache).filter(LLMCache.created_at < cleanup_date).delete()
            session.commit()
            self.logger.info("Cleaned up old cache entries")

    def get_translation(
        self, text: str, translator_type: str, **params
    ) -> Optional[str]:
        """获取翻译缓存"""
        if not text:
            raise ValueError("Text cannot be empty")
        self._validate_translator_type(translator_type)

        hash_key = self._generate_hash(text, params)
        try:
            with self.db_manager.get_session() as session:
                result = (
                    session.query(TranslationCache)
                    .filter_by(content_hash=hash_key, translator_type=translator_type)
                    .first()
                )
                return result.translated_text if result else None
        except Exception as e:
            self.logger.error(f"Error getting translation cache: {str(e)}")
            return None

    def set_translation(
        self, text: str, translated_text: str, translator_type: str, **params
    ):
        """设置翻译缓存"""
        if not text or not translated_text:
            raise ValueError("Text and translated text cannot be empty")
        self._validate_translator_type(translator_type)

        hash_key = self._generate_hash(text, params)
        try:
            with self.db_manager.get_session() as session:
                translation = TranslationCache(
                    source_text=text,
                    translated_text=translated_text,
                    translator_type=translator_type,
                    params=params,
                    content_hash=hash_key,
                )
                session.add(translation)
                session.commit()
                self.logger.info(f"Cached translation for {translator_type}")
        except Exception as e:
            self.logger.error(f"Error setting translation cache: {str(e)}")
            raise

    def get_llm_result(self, prompt: str, model_name: str, **params) -> Optional[str]:
        """获取LLM结果缓存"""
        if not prompt or not model_name:
            raise ValueError("Prompt and model name cannot be empty")

        hash_key = self._generate_hash(prompt, params)
        try:
            with self.db_manager.get_session() as session:
                result = (
                    session.query(LLMCache)
                    .filter_by(content_hash=hash_key, model_name=model_name)
                    .first()
                )
                return result.result if result else None
        except Exception as e:
            self.logger.error(f"Error getting LLM cache: {str(e)}")
            return None

    def set_llm_result(self, prompt: str, result: str, model_name: str, **params):
        """设置LLM结果缓存"""
        if not prompt or not result or not model_name:
            raise ValueError("Prompt, result and model name cannot be empty")

        hash_key = self._generate_hash(prompt, params)
        try:
            with self.db_manager.get_session() as session:
                llm_result = LLMCache(
                    prompt=prompt,
                    result=result,
                    model_name=model_name,
                    params=params,
                    content_hash=hash_key,
                )
                session.add(llm_result)
                session.commit()
                self.logger.info(f"Cached LLM result for {model_name}")
        except Exception as e:
            self.logger.error(f"Error setting LLM cache: {str(e)}")
            raise

    def update_usage_stats(
        self, operation_type: str, service_name: str, token_count: int = 0
    ):
        """更新使用统计"""
        self._validate_operation_type(operation_type)
        if not service_name:
            raise ValueError("Service name cannot be empty")
        if token_count < 0:
            raise ValueError("Token count cannot be negative")

        try:
            with self.db_manager.get_session() as session:
                stats = (
                    session.query(UsageStatistics)
                    .filter_by(operation_type=operation_type, service_name=service_name)
                    .first()
                )

                if not stats:
                    stats = UsageStatistics(
                        operation_type=operation_type,
                        service_name=service_name,
                        call_count=0,
                        token_count=0,
                    )
                    session.add(stats)

                stats.call_count += 1
                stats.token_count += token_count
                stats.last_updated = datetime.utcnow()
                session.commit()
                self.logger.info(
                    f"Updated usage stats for {operation_type}:{service_name}"
                )
        except Exception as e:
            self.logger.error(f"Error updating usage stats: {str(e)}")
            raise

    def get_usage_stats(
        self, operation_type: Optional[str] = None
    ) -> Dict[str, Dict[str, Any]]:
        """获取使用统计信息"""
        if operation_type:
            self._validate_operation_type(operation_type)

        try:
            with self.db_manager.get_session() as session:
                query = session.query(UsageStatistics)
                if operation_type:
                    query = query.filter_by(operation_type=operation_type)

                stats = query.all()
                return {
                    f"{stat.operation_type}_{stat.service_name}": {
                        "call_count": stat.call_count,
                        "token_count": stat.token_count,
                        "last_updated": stat.last_updated.isoformat(),
                    }
                    for stat in stats
                }
        except Exception as e:
            self.logger.error(f"Error getting usage stats: {str(e)}")
            return {}

    def get_asr_result(self, crc32_hex: str, asr_type: str) -> Optional[dict]:
        """获取语音识别缓存结果"""
        if not crc32_hex or not asr_type:
            raise ValueError("CRC32 hex and ASR type cannot be empty")

        try:
            with self.db_manager.get_session() as session:
                result = (
                    session.query(ASRCache)
                    .filter_by(crc32_hex=crc32_hex, asr_type=asr_type)
                    .first()
                )
                return result.result_data if result else None
        except Exception as e:
            self.logger.error(f"Error getting ASR cache: {str(e)}")
            return None

    def set_asr_result(self, crc32_hex: str, asr_type: str, result_data: dict):
        """设置语音识别缓存结果"""
        if not crc32_hex or not asr_type or not result_data:
            raise ValueError("CRC32 hex, ASR type and result data cannot be empty")

        try:
            with self.db_manager.get_session() as session:
                # 检查是否已存在相同的缓存
                existing_cache = (
                    session.query(ASRCache)
                    .filter_by(crc32_hex=crc32_hex, asr_type=asr_type)
                    .first()
                )

                if existing_cache:
                    existing_cache.result_data = result_data
                    existing_cache.updated_at = datetime.utcnow()
                else:
                    asr_cache = ASRCache(
                        crc32_hex=crc32_hex, asr_type=asr_type, result_data=result_data
                    )
                    session.add(asr_cache)

                session.commit()
                self.logger.info(f"Cached ASR result for {asr_type}")
        except Exception as e:
            self.logger.error(f"Error setting ASR cache: {str(e)}")
            raise
