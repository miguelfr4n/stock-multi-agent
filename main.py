import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import uvicorn
from database import init_db

if __name__ == "__main__":
    print("Inicializando banco de dados...")
    init_db()
    print("Banco de dados pronto.")
    print("\nIniciando servidor na porta 8080...")
    print("Acesse: http://localhost:8081/docs")
    print("Chat:   POST http://localhost:8081/chat\n")
    uvicorn.run("api:app", host="0.0.0.0", port=8081, reload=True)
