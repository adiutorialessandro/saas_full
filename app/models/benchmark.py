from app.extensions import db

class SectorBenchmark(db.Model):
    __tablename__ = 'sector_benchmarks'
    id = db.Column(db.Integer, primary_key=True)
    sector_name = db.Column(db.String(100), unique=True, nullable=False)
    margine_lordo_target = db.Column(db.Float)
    conversione_target = db.Column(db.Float)
    break_even_sano = db.Column(db.Float)
    runway_minima = db.Column(db.Integer)

    def __repr__(self):
        return f'<Benchmark {self.sector_name}>'
