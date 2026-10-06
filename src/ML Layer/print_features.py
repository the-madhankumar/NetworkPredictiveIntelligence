from joblib import load
model = load(r'D:\Training Project\Project 2\Dataset\analytics\ML_LAYER\risk_classifier\risk_classifier.joblib')
feature_names = model.feature_names_in_
print(feature_names)