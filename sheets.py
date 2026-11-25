import os
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

class SheetsLogger:
    HEADERS={
      "Users":["user_id","username","first_name","created_at"],
      "Videos":["user_id","prompt","seconds","credits","file_path","status","created_at"],
      "Payments":["payment_id","user_id","amount","status","proof_file_id","created_at","reviewed_at"],
      "Transactions":["tx_id","user_id","amount","reason","balance_after","created_at"],
      "Subscriptions":["sub_id","user_id","plan","credits","starts_at","expires_at","payment_id"]}
    def __init__(self,sheet_id,credential_path):
        self.enabled=bool(sheet_id and os.path.isfile(credential_path)); self.service=None; self.sheet_id=sheet_id
        if self.enabled:
            creds=Credentials.from_service_account_file(credential_path,scopes=["https://www.googleapis.com/auth/spreadsheets"])
            self.service=build("sheets","v4",credentials=creds,cache_discovery=False); self._setup()
    def _setup(self):
        meta=self.service.spreadsheets().get(spreadsheetId=self.sheet_id).execute()
        existing={x["properties"]["title"] for x in meta.get("sheets",[])}
        req=[{"addSheet":{"properties":{"title":n}}} for n in self.HEADERS if n not in existing]
        if req: self.service.spreadsheets().batchUpdate(spreadsheetId=self.sheet_id,body={"requests":req}).execute()
        for tab,headers in self.HEADERS.items():
            vals=self.service.spreadsheets().values().get(spreadsheetId=self.sheet_id,range=f"{tab}!A1:Z1").execute().get("values",[])
            if not vals:
                self.service.spreadsheets().values().update(spreadsheetId=self.sheet_id,range=f"{tab}!A1",valueInputOption="RAW",body={"values":[headers]}).execute()
    def append(self,tab,values):
        if not self.enabled: return
        try:
            self.service.spreadsheets().values().append(spreadsheetId=self.sheet_id,range=f"{tab}!A:Z",
                valueInputOption="RAW",insertDataOption="INSERT_ROWS",
                body={"values":[[str(v) if v is not None else "" for v in values]]}).execute()
        except Exception:
            # SQLite is authoritative; temporary Sheets failures must not block bot actions.
            pass
