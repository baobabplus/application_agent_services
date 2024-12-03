import xmlrpc.client

from app.core.odoo_config import settings


class OdooAPI:
    def __init__(self, uuid=None):
        self.url = settings.odoo_url
        self.db = settings.odoo_db
        self.username = settings.odoo_username
        self.password = settings.odoo_password
        self.common = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common")
        self.uid = settings.odoo_uuid or self._get_uuid()
        self.models = self._get_models()

    def _get_uuid(self):
        return self.common.authenticate(self.db, self.username, self.password, {})

    def _get_models(self):
        if self.uid:
            return xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/object")
        else:
            raise Exception("Connection failed.")

    def search_records(
        self, model, domain, fields=False, offset=0, limit=False, order=False
    ):
        if not self.models:
            raise Exception("Please connect to Odoo first.")
        attributes = {"fields": fields, "offset": offset}
        if offset and not order:
            order = "id desc"
        if order:
            attributes["order"] = order
        if limit != -1:
            attributes["limit"] = limit
        return self.models.execute_kw(
            self.db,
            self.uid,
            self.password,
            model,
            "search_read",
            [domain],
            attributes,
        )

    def create_record(self, model, values, context=None):
        if context is None:
            context = {}
        if not self.models:
            raise Exception("Please connect to Odoo first.")
        return self.models.execute_kw(
            self.db, self.uid, self.password, model, "create", [values], context
        )

    def update_record(self, model, record_id, values):
        if not self.models:
            raise Exception("Please connect to Odoo first.")
        return self.models.execute_kw(
            self.db, self.uid, self.password, model, "write", [[record_id], values]
        )

    def delete_record(self, model, record_ids):
        if not self.models:
            raise Exception("Please connect to Odoo first.")
        return self.models.execute_kw(
            self.db, self.uid, self.password, model, "unlink", [record_ids]
        )
