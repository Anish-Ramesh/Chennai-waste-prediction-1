#  Household Source Segregation Prediction - Chennai

This project predicts the **percentage of household source segregation** in various wards of Chennai using multiple regression models. It provides insights into which machine learning models are most effective for this urban waste management dataset.

---

##  Dataset Description

The dataset includes the following fields:

- `City_Name`: City name (all values are "Chennai")
- `Zone_Name`: Zone to which the ward belongs (categorical)
- `Ward_No`: Numeric identifier for the ward
- `Total_Households`: Total number of households in a ward
- `Covered_Households`: Number of households covered under the scheme
- `HH_Source_Segregation`: Percentage of household source segregation

The column `Ward Name` was dropped due to missing values and lack of variance.

---

##  Installation

To run the project, make sure you have Python 3.7+ and install the dependencies using:

```bash
pip install -r requirements.txt
