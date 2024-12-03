class BaseAPI:
    def get_available_country(self):
        countries = [
            {
                "name": "Nigeria",
                "flag_url": "https://flagcdn.com/w320/ng.png",
                "dial_code": "+234",
            },
            {
                "name": "Democratic Republic of Congo",
                "flag_url": "https://flagcdn.com/w320/cd.png",
                "dial_code": "+243",
            },
            {
                "name": "Madagascar",
                "flag_url": "https://flagcdn.com/w320/mg.png",
                "dial_code": "+261",
            },
            {
                "name": "Senegal",
                "flag_url": "https://flagcdn.com/w320/sn.png",
                "dial_code": "+221",
            },
        ]
        return {"count": len(countries), "records": countries}
