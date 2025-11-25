"""
ChromaDB 서비스
문서 저장 및 검색 (RAG) 기능 제공
"""

import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional
from uuid import UUID
import logging

logger = logging.getLogger(__name__)


class ChromaService:
    """ChromaDB를 사용한 벡터 DB 서비스"""
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        """
        ChromaDB 클라이언트 초기화
        
        Args:
            persist_directory: ChromaDB 데이터 저장 경로
        """
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        self.collection = self.client.get_or_create_collection(
            name="documents",
            metadata={"hnsw:space": "cosine"}
        )
        
        logger.info(f"ChromaDB initialized with collection: documents")
    
    def add_document(
        self, 
        document_id: UUID, 
        content: str, 
        metadata: Optional[Dict] = None
    ) -> None:
        """
        문서를 ChromaDB에 저장
        
        Args:
            document_id: 문서 고유 ID
            content: 문서 내용
            metadata: 문서 메타데이터
        """
        doc_id = str(document_id)
        
        if metadata is None:
            metadata = {}
        
        metadata["document_id"] = doc_id
        
        try:
            self.collection.add(
                documents=[content],
                ids=[doc_id],
                metadatas=[metadata]
            )
            logger.info(f"Document {doc_id} added to ChromaDB")
        except Exception as e:
            logger.error(f"Failed to add document {doc_id}: {e}")
            raise
    
    def add_document_chunks(
        self,
        document_id: UUID,
        chunks: List[str],
        metadatas: Optional[List[Dict]] = None,
        images: Optional[List[Dict]] = None
    ) -> None:
        """
        문서를 청크 단위로 저장 (멀티모달 지원)
        
        Args:
            document_id: 문서 고유 ID
            chunks: 문서 청크 리스트
            metadatas: 각 청크의 메타데이터 리스트
            images: 이미지 정보 리스트 [{data: base64, page: int, caption: str}]
        """
        doc_id = str(document_id)
        
        if metadatas is None:
            metadatas = [{} for _ in chunks]
        
        for i, metadata in enumerate(metadatas):
            metadata["document_id"] = doc_id
            metadata["chunk_index"] = i
        
        if images:
            image_info = {
                "has_images": True,
                "image_count": len(images),
                "image_pages": [img.get("page", 0) for img in images]
            }
            for metadata in metadatas:
                metadata.update(image_info)
        
        chunk_ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
        
        try:
            self.collection.add(
                documents=chunks,
                ids=chunk_ids,
                metadatas=metadatas
            )
            logger.info(f"Document {doc_id} added in {len(chunks)} chunks")
        except Exception as e:
            logger.error(f"Failed to add document chunks for {doc_id}: {e}")
            raise
    
    def search_by_document_id(
        self,
        document_id: UUID,
        limit: int = 10
    ) -> List[str]:
        """
        특정 문서 ID로 청크 검색
        
        Args:
            document_id: 문서 ID
            limit: 반환할 최대 청크 수
            
        Returns:
            문서 청크 리스트
        """
        doc_id = str(document_id)
        
        try:
            # document_id로 필터링
            results = self.collection.get(
                where={"document_id": doc_id},
                limit=limit
            )
            
            if results and "documents" in results:
                return results["documents"]
            return []
        except Exception as e:
            logger.error(f"Failed to search document {doc_id}: {e}")
            return []
    
    def search_similar(
        self,
        query: str,
        n_results: int = 5,
        document_id: Optional[UUID] = None
    ) -> List[Dict]:
        """
        유사한 문서 청크 검색 (RAG)
        
        Args:
            query: 검색 쿼리
            n_results: 반환할 결과 수
            document_id: 특정 문서 내에서만 검색 (Optional)
            
        Returns:
            검색 결과 리스트 (document, metadata, distance)
        """
        where_filter = None
        if document_id:
            where_filter = {"document_id": str(document_id)}
        
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_filter
            )
            
            # 결과 포맷팅
            formatted_results = []
            if results and "documents" in results and results["documents"]:
                for i, doc in enumerate(results["documents"][0]):
                    formatted_results.append({
                        "document": doc,
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        "distance": results["distances"][0][i] if "distances" in results else None
                    })
            
            return formatted_results
        except Exception as e:
            logger.error(f"Failed to search similar documents: {e}")
            return []
    
    def delete_document(self, document_id: UUID) -> None:
        """
        문서 삭제
        
        Args:
            document_id: 삭제할 문서 ID
        """
        doc_id = str(document_id)
        
        try:
            results = self.collection.get(
                where={"document_id": doc_id}
            )
            
            if results and "ids" in results and results["ids"]:
                self.collection.delete(ids=results["ids"])
                logger.info(f"Document {doc_id} deleted from ChromaDB")
        except Exception as e:
            logger.error(f"Failed to delete document {doc_id}: {e}")
            raise
    
    def reset_collection(self) -> None:
        """컬렉션 초기화 (개발용)"""
        try:
            self.client.delete_collection(name="documents")
            self.collection = self.client.create_collection(
                name="documents",
                metadata={"hnsw:space": "cosine"}
            )
            logger.info("Collection reset successfully")
        except Exception as e:
            logger.error(f"Failed to reset collection: {e}")
            raise


# 싱글톤 인스턴스
_chroma_service: Optional[ChromaService] = None


def get_chroma_service() -> ChromaService:
    """ChromaService 싱글톤 인스턴스 반환"""
    global _chroma_service
    if _chroma_service is None:
        _chroma_service = ChromaService()
    return _chroma_service
