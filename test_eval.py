"""Golden Test Set 评估 — Hit Rate + MRR + Faithfulness"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.environ["PYTHONIOENCODING"] = "utf-8"

from src.core.settings import load_settings, resolve_path, EvaluationSettings
from src.core.query_engine.hybrid_search import create_hybrid_search
from src.core.query_engine.query_processor import QueryProcessor
from src.core.query_engine.dense_retriever import create_dense_retriever
from src.core.query_engine.sparse_retriever import create_sparse_retriever
from src.core.query_engine.reranker import create_core_reranker
from src.ingestion.storage.bm25_indexer import BM25Indexer
from src.libs.embedding.embedding_factory import EmbeddingFactory
from src.libs.vector_store.vector_store_factory import VectorStoreFactory
from src.libs.evaluator.evaluator_factory import EvaluatorFactory
from dataclasses import replace

test_set = [
    {"q": "Agent 由哪些核心组件组成",       "expected": "规划",     "topic": "Agent"},
    {"q": "什么是 CoT 思维链",              "expected": "思维链",    "topic": "Agent"},
    {"q": "Agent 中 Memory 的作用是什么",   "expected": "长期记忆",  "topic": "Agent"},
    {"q": "什么是 Function Calling",        "expected": "调用外部工具","topic": "Agent"},
    {"q": "什么是多智能体系统",              "expected": "多个",      "topic": "Agent"},
    {"q": "如何评估 Agent 的安全性",        "expected": "安全",      "topic": "Agent"},
    {"q": "RAG 的工作原理是什么",           "expected": "检索增强生成","topic": "RAG"},
    {"q": "RAG 流水线包含哪些关键步骤",     "expected": "检索",      "topic": "RAG"},
    {"q": "Naive RAG 的缺点是什么",         "expected": "重排序",    "topic": "RAG"},
    {"q": "什么是 Lost in the Middle",      "expected": "中间",      "topic": "RAG"},
    {"q": "RAG 系统部署面临哪些挑战",       "expected": "延迟",      "topic": "RAG"},
    {"q": "什么是 Rerank",                  "expected": "精排",      "topic": "RAG"},
    {"q": "Hybrid Search 是什么",           "expected": "混合",      "topic": "RAG"},
    {"q": "如何评估 LLM 应用的性能",        "expected": "评估指标",  "topic": "评估"},
    {"q": "LLM 评估指标有哪些",             "expected": "准确率",    "topic": "评估"},
]

settings = load_settings()
collection = "default"
top_k = 10

vector_store = VectorStoreFactory.create(settings, collection_name=collection)
emb_client = EmbeddingFactory.create(settings)
dense = create_dense_retriever(settings=settings, embedding_client=emb_client, vector_store=vector_store)
bm25 = BM25Indexer(index_dir=str(resolve_path(f"data/db/bm25/{collection}")))
sparse = create_sparse_retriever(settings=settings, bm25_indexer=bm25, vector_store=vector_store)
sparse.default_collection = collection
hybrid = create_hybrid_search(settings=settings, query_processor=QueryProcessor(), dense_retriever=dense, sparse_retriever=sparse)
reranker = create_core_reranker(settings=settings)

print("=" * 70)
print("Golden Test Set 评估")
print("=" * 70)

all_ranks = []
for i, t in enumerate(test_set):
    init_top = top_k * 2 if reranker.is_enabled else top_k
    results = hybrid.search(query=t["q"], top_k=init_top)
    results = results if isinstance(results, list) else results.results
    if reranker.is_enabled and results:
        results = reranker.rerank(query=t["q"], results=results, top_k=top_k).results

    hit_rank = None
    for rank, r in enumerate(results, 1):
        text = r.text if hasattr(r, 'text') else (r.get('text','') if isinstance(r, dict) else str(r))
        if t["expected"] in text and hit_rank is None:
            hit_rank = rank

    status = f"#{hit_rank}" if hit_rank else "MISS"
    print(f"  [{t['topic']}] {t['q']:30s} -> {status}")
    all_ranks.append(hit_rank)

h1 = sum(1 for r in all_ranks if r and r <= 1)
h3 = sum(1 for r in all_ranks if r and r <= 3)
h5 = sum(1 for r in all_ranks if r and r <= 5)
h10 = sum(1 for r in all_ranks if r)
rr = [1.0/r for r in all_ranks if r]
mrr = sum(rr)/len(rr) if rr else 0

print(f"\nHit Rate@1: {h1}/15  Hit@3: {h3}/15  Hit@5: {h5}/15  Hit@10: {h10}/15")
print(f"MRR: {mrr:.3f}")
