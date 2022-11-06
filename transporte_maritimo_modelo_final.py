# -*- coding: utf-8 -*-
"""
Created on Sat Nov  5 01:06:26 2022

@author: davidson.lima
"""

# Objetivo:
# Otimizar consumo de combustível, logo o trajeto, de produtos para plataformas,
# dada uma ordem

import os
import numpy as np
import pandas as pd
from geographiclib.geodesic import Geodesic
import more_itertools as mit
import requests
import json

mar_db = pd.read_csv(r'transporte_maritimo_modelo1_dados.csv', sep=",")
#mar_db.describe()
#mar_db.info()

ENDPOINT = 'http://sealog-api.ismalenascimento.com/route'

pd.set_option('display.max_columns', 50)
pd.set_option('display.max_rows', 1000)

def CalculoDistancia(lat1, lon1, lat2, lon2):
    ans = Geodesic.WGS84.Inverse(lat1, lon1, lat2, lon2)
    distancia = ans["s12"] / 1000
    return distancia

def EfeitoClima(alturaOnda, tempoPercurso, velocidade):
    velocidadeNew = 0
    tempoPercursoNew = 0
    if alturaOnda <= 2.5:
        velocidadeNew = velocidade-0
        tempoPercursoNew = tempoPercurso*(1+0)
    elif alturaOnda > 2.5 and alturaOnda <= 3.5:
        velocidadeNew = velocidade-0
        tempoPercursoNew = tempoPercurso*(1+0.2)
    elif alturaOnda > 3.5 and alturaOnda <= 4.5:
        velocidadeNew = velocidade-2
        tempoPercursoNew = tempoPercurso*(1+0.3)
    else:
        velocidadeNew = None
        tempoPercursoNew = None
        
    return velocidadeNew, tempoPercursoNew

def CalculoCombustivel(distancia):
    taxaConsumo = 16/24 # m3/dia => m3/h
    velocidade = 13*0.51*3.6 # nos => m/s => km/h
    precoDiesel = 6.72*1000 # R$/L => R$/m3
    
    alturaOnda = 2.0 # m
    tempoPercurso = distancia/velocidade # h
    velocidade, tempoRecurso = EfeitoClima(alturaOnda, tempoPercurso, velocidade)
    
    consumoDiesel = taxaConsumo * tempoPercurso # m3
    gastoDiesel = consumoDiesel*precoDiesel # R$
    return consumoDiesel, gastoDiesel

latlonvalues = mar_db.iloc[:, 3:5]
lettervalues = list(mar_db.iloc[1:, -1])
letterpermutations = list(mit.distinct_permutations(lettervalues))
letterpermutations = [['A'] + list(x) + ['A'] for x in letterpermutations]

data = []
for i, perm in enumerate(letterpermutations):
    j = 0
    while j < len(perm)-1:
        rota = 'Viagem {0}'.format(i+1)
        rotaGlobal = ''.join(letterpermutations[i])
        origem = perm[j]
        destino = perm[j+1]
        latitudeOrigem = float(mar_db.loc[mar_db['Ponto'] == origem]['Latitude'])
        longitudeOrigem = float(mar_db.loc[mar_db['Ponto'] == origem]['Longitude'])
        latitudeDestino = float(mar_db.loc[mar_db['Ponto'] == destino]['Latitude'])
        longitudeDestino = float(mar_db.loc[mar_db['Ponto'] == destino]['Longitude'])
        distancia = CalculoDistancia(latitudeOrigem, longitudeOrigem,
                                      latitudeDestino, longitudeDestino)
        consumoDiesel, gastoDiesel = CalculoCombustivel(distancia)
        data.append([rota, origem, destino,
                     latitudeOrigem, longitudeOrigem,
                     latitudeDestino, longitudeDestino,
                     rotaGlobal, distancia,
                     consumoDiesel,
                     gastoDiesel])
        j += 1
        
combinacoes = pd.DataFrame(data=data, columns=['Rota', 'Origem', 'Destino',
                                               'LatitudeOrigem', 'LongitudeOrigem',
                                               'LatitudeDestino', 'LongitudeDestino',
                                               'RotaGlobal', 'Distancia (Km)',
                                               'ConsumoDiesel (m3)',
                                               'GastoDiesel (R$)'])

combinacoesAgregado = combinacoes.groupby(by='RotaGlobal').sum()
combinacoesAgregadoOrdenado = combinacoesAgregado.iloc[:,-3:].sort_values(['GastoDiesel (R$)'], ascending=True)
combinacoesAgregadoOrdenado = combinacoesAgregadoOrdenado.drop_duplicates(['Distancia (Km)'])

# Se quiser retornar todo o raw data
# combinacoes = combinacoes.to_json()

rotas = []
for combinacao in combinacoes.values:
    origem = combinacao[1]
    destino = combinacao[2]
    distancia = combinacao[8]
    rota = {
        "name": "brown",
        "originAddress": origem,
        "originDatetime": "",
        "destinationAddress": destino,
        "destinationDatetime": "",
        "distance": distancia,
        "travelId": "1",
    }
    rotas.append(rota)

rotasJSON = json.dumps(rotas)
