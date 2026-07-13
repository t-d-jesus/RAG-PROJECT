from app.vectorstore.pgvector_store import (
    get_connection,
    initialize_database,
)


def main() -> None:
    initialize_database()

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT extname, extversion
                FROM pg_extension
                WHERE extname = 'vector'
                """
            )

            extension = cursor.fetchone()

            cursor.execute(
                """
                SELECT to_regclass(
                    'public.vector_documents'
                )
                """
            )

            table = cursor.fetchone()

    print(f"Extensão: {extension}")
    print(f"Tabela: {table}")
    print("pgvector inicializado com sucesso")


if __name__ == "__main__":
    main()
