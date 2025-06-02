
# src/outlier_detector.py
import numpy as np

class OutlierDetector:
    def _init_(self, method="simple_threshold"):
        self.method = method
        self.threshold = 10000.0 # Example threshold for total_inr in INR
        print(f"OutlierDetector initialized with method: {self.method} (Currently a mock service)")

    def detect_outlier(self, data_point, field_name="total_inr"):
        """
        Mocks anomaly detection.
        In a real scenario, this would use statistical models (e.g., IQR, Z-score, isolation forest).
        """
        print(f"  (Outlier Detection: Mocking for {field_name})")
        if field_name == "total_inr" and data_point is not None:
            if data_point > self.threshold:
                return {"is_outlier": True, "reason": f"Total INR ({data_point:.2f}) exceeds threshold ({self.threshold:.2f})."}
        return {"is_outlier": False, "reason": "Within normal range (mocked)."}

    def learn_from_data(self, historical_data):
        """
        Mocks learning from historical data to set thresholds or train models.
        """
        print("  (Outlier Detector Learning: Mocking)")
        if historical_data and isinstance(historical_data, list) and historical_data:
            # Example: update threshold based on average + 2*stddev
            total_inr_values = [d['total_inr'] for d in historical_data if d and 'total_inr' in d and d['total_inr'] is not None]
            if total_inr_values:
                mean_val = np.mean(total_inr_values)
                std_val = np.std(total_inr_values)
                self.threshold = mean_val + 2 * std_val
                print(f"  (Outlier Detector Learned: New threshold for total_inr: {self.threshold:.2f})")