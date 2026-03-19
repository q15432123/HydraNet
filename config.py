import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
SOLANA_RPC_URL = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
HELIUS_API_KEY = os.getenv("HELIUS_API_KEY", "")
DATABASE_PATH = os.getenv("DATABASE_PATH", "hydranet.db")
CHROMADB_PATH = os.getenv("CHROMADB_PATH", "./chroma_data")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
EVOLUTION_INTERVAL = int(os.getenv("EVOLUTION_INTERVAL_SECONDS", "300"))
MAX_AGENTS = int(os.getenv("MAX_AGENTS", "50"))

# Solana constants
SOL_DECIMALS = 9
LAMPORTS_PER_SOL = 1_000_000_000

# Agent evolution
MIN_SCORE_THRESHOLD = 0.3
REPLICATION_SCORE_THRESHOLD = 0.8
MUTATION_RATE = 0.15
