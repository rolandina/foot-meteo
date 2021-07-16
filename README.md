# *foot-meteo: Championships data base with meteo data* 

## *What is does*
In this study project we create data base sqlite local with the data taken from the site [l'Équipe](https://www.lequipe.fr/)

You can look at the data base structure in the file championship.sql
or in the .png

The architecture of the data base was made in [DBdesigner](https://app.dbdesigner.net) and after was imported into our code.

Code is written in python.

All dependencies you need to run this project are listed in environment.yml


## General Prerequisites (for running and building)

* [Anaconda](https://www.anaconda.com/products/individual)
* [GitHub](https://github.com)

After installing anaconda and python you have to set your environment with environment.yml file

```bash
conda env create -f environment.yml
conda activate house_predict
```

## To build and run 

```
# Clone this repository 
git clone https://github.com/rolandina/house-price-prediction-app.git
```

```
# To run streamlit app on your laptop 
cd project_with_weather_from_csv
streamlit run app.py
```

## Contributing

The architecture of the data base was made in [DBdesigner](https://app.dbdesigner.net) 
The data taken from the site [l'Équipe](https://www.lequipe.fr/)

If you have any questions please reach one of the authors of the project:

* [Hugo FUGERAY](https://github.com/hugofgry)
* [Nina SMIRNOVA](https://github.com/rolandina)
* [Nouha EL ABED](https://github.com/NOUHA90)
* [Michael KRYSZTOFIAK](https://github.com/art2mkl )
