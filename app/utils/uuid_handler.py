from uuid import UUID


class UUIDHandler:

    def convert_id_to_uuid(self, book_dict):
        if isinstance(book_dict["id"], int):
            book_dict["id"] = UUID(int=book_dict["id"])
        return book_dict
