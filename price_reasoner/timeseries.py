from prophet import Prophet
import pandas as pd

class TimeSeriesDecomposer:
    """Prophet-based time series decomposition"""

    def decompose(self, price_data: list[dict]) -> dict:
        """
        price_data: [{"ds": "2023-01-01", "y": 100.0}, ...]
        Returns trend/seasonality/residual with dates
        """
        df = pd.DataFrame(price_data)
        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=False,
            daily_seasonality=False,
        )
        model.fit(df)
        forecast = model.predict(df)

        return {
            "trend": forecast["trend"].tolist(),
            "seasonality": forecast["yearly"].tolist() if "yearly" in forecast.columns else [],
            "residual": forecast["residual"].tolist() if "residual" in forecast.columns else [],
            "dates": forecast["ds"].dt.strftime("%Y-%m-%d").tolist(),
        }

    def extract_residual_with_dates(self, price_data: list[dict]) -> list[dict]:
        """Return residual series with dates for AI attribution"""
        result = self.decompose(price_data)
        return [
            {"date": result["dates"][i], "residual": result["residual"][i]}
            for i in range(len(result["dates"]))
        ]