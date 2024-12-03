from .client import OdooAPI


class Models:
    def __init__(self, client: OdooAPI, model_name: str):
        self.client = client
        self.model_name = model_name

    def browse(self, id):
        res_id = self.client.search_records(self.model_name, [["id", "=", id]], ["id"])
        if res_id:
            return res_id[0]["id"]
        return False

    def search(
        self,
        domain,
        fields=False,
        offset: int = 0,
        limit: int = 80,
        order: str = "id asc",
    ):
        return self.client.search_records(
            self.model_name, domain, fields, offset, limit, order
        )

    def create(self, payload, context=None):
        if context is None:
            context = {}
        return self.client.create_record(self.model_name, payload, context)

    def write(self, id, payload):
        return self.client.update_record(self.model_name, id, payload)

    def unlink(self, ids):
        return self.client.delete_record(self.model_name, ids)

    def get_order_column(self):
        return ["id", "create_date"]
