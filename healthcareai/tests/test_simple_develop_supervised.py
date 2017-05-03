import sys
import unittest
from contextlib import contextmanager
from io import StringIO

from healthcareai.common.healthcareai_error import HealthcareAIError
from healthcareai.trainer import SupervisedModelTrainer
import healthcareai.tests.helpers as helpers
from healthcareai.trained_models.trained_supervised_model import TrainedSupervisedModel


class TestSimpleDevelopSupervisedModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        df = helpers.load_sample_dataframe()

        # Drop columns that won't help machine learning
        columns_to_remove = ['PatientID', 'InTestWindowFLG']
        df.drop(columns_to_remove, axis=1, inplace=True)

        cls.classification = SupervisedModelTrainer(dataframe=df,
                                                    predicted_column='ThirtyDayReadmitFLG',
                                                    model_type='classification',
                                                    impute=True,
                                                    grain_column='PatientEncounterID',
                                                    verbose=False)
        cls.regression = SupervisedModelTrainer(df,
                                                      'SystolicBPNBR',
                                                      'regression',
                                                grain_column='PatientEncounterID',
                                                impute=True,
                                                verbose=False)

    def test_knn(self):
        trained_knn = self.classification.knn()

        result = trained_knn.metrics()
        self.assertIsInstance(trained_knn, TrainedSupervisedModel)

        helpers.assertBetween(self, 0.5, 0.6, result['roc_auc'])
        helpers.assertBetween(self, 0.79, 0.95, result['accuracy'])

    def test_random_forest_classification(self):
        trained_random_forest = self.classification.random_forest_classification()
        result = trained_random_forest.metrics()
        self.assertIsInstance(trained_random_forest, TrainedSupervisedModel)

        helpers.assertBetween(self, 0.65, 0.8, result['roc_auc'])
        helpers.assertBetween(self, 0.8, 0.95, result['accuracy'])

    def test_linear_regression(self):
        trained_linear_model = self.regression.linear_regression()
        self.assertIsInstance(trained_linear_model, TrainedSupervisedModel)

        result = trained_linear_model.metrics()

        expected_mse = 638
        self.assertAlmostEqual(expected_mse, result['mean_squared_error'], places=-1)

        expected_mae = 20
        self.assertAlmostEqual(expected_mae, result['mean_absolute_error'], places=-1)

    def test_random_forest_regression(self):
        trained_rf_regressor = self.regression.random_forest_regression()
        self.assertIsInstance(trained_rf_regressor, TrainedSupervisedModel)

        result = trained_rf_regressor.metrics()

        expected_mse = 630
        self.assertAlmostEqual(expected_mse, result['mean_squared_error'], places=-2)

        expected_mae = 18
        self.assertAlmostEqual(expected_mae, result['mean_absolute_error'], places=-1)

    def test_logistic_regression(self):
        trained_lr = self.classification.logistic_regression()
        self.assertIsInstance(trained_lr, TrainedSupervisedModel)

        result = trained_lr.metrics()

        # TODO is this even a valid test at a 0.5 auc?
        helpers.assertBetween(self, 0.5, 0.6, result['roc_auc'])
        helpers.assertBetween(self, 0.79, 0.95, result['accuracy'])

    def test_ensemble_classification(self):
        trained_ensemble = self.classification.ensemble()
        self.assertIsInstance(trained_ensemble, TrainedSupervisedModel)

        result = trained_ensemble.metrics()

        helpers.assertBetween(self, 0.7, 0.8, result['roc_auc'])
        helpers.assertBetween(self, 0.79, 0.95, result['accuracy'])

    def test_ensemble_regression(self):
        self.assertRaises(HealthcareAIError, self.regression.ensemble)

    def test_linear_regression_raises_error_on_missing_columns(self):
        training_df = helpers.load_sample_dataframe()

        # Drop columns that won't help machine learning
        training_df.drop(['PatientID', 'InTestWindowFLG'], axis=1, inplace=True)

        # # Train the linear regression model
        trained_linear_model = self.regression.linear_regression()

        # Load a new df for predicting
        prediction_df = helpers.load_sample_dataframe()

        # Drop columns that model expects
        prediction_df.drop('GenderFLG', axis=1, inplace=True)

        # Make some predictions
        self.assertRaises(HealthcareAIError, trained_linear_model.make_predictions, prediction_df)


@contextmanager
def captured_output():
    """
    A quick and dirty context manager that captures STDOUT and STDERR to enable testing of functions that print() things
    """
    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err


if __name__ == '__main__':
    unittest.main()
