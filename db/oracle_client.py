from datetime import datetime
from typing import List, Dict
from dataclasses import dataclass
from oracledb import connect as oracle_connect

@dataclass
class ImagePath:
    nro_smf: str
    path: str
    capture_date: datetime
    cod_unicom: str
    nis_rad: str
    ruta: str
    tip_foto: str
    num_itin: str

class OracleClient:
    def __init__(self, config: Dict):
        self.config = config
        
    def get_connection(self):
        return oracle_connect(
            user=self.config['user'],
            password=self.config['password'],
            dsn=f"{self.config['host']}:{self.config['port']}/{self.config['database']}"
        )

    def fetch_image_paths(self, process_date: datetime) -> List[ImagePath]:
        oracle_date = process_date.strftime('%y-%m-%d')
        query = """
            SELECT NRO_SMF, PATH, CAPTURE_DATE, COD_UNICOM, NIS_RAD, RUTA, TIP_FOTO, NUM_ITIN
            FROM FACSITIO.PICTURES
            WHERE TRUNC(F_ACTUAL) = TO_DATE(:1, 'YY-MM-DD')
            AND TIP_FOTO in('CF001')
            AND IND_ARCHIVO = 1
        """
        
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, [oracle_date])
                results = cursor.fetchall()
                
                return [
                    ImagePath(
                        nro_smf=str(row[0]),
                        path=str(row[1]),
                        capture_date=row[2],
                        cod_unicom=str(row[3]),
                        nis_rad=str(row[4]),
                        ruta=str(row[5]),
                        tip_foto=str(row[6]),
                        num_itin=str(row[7])
                    )
                    for row in results
                ]