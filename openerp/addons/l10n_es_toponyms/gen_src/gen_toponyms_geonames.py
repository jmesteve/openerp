# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2013 Serv. Tecnol. Avanzados (http://www.serviciosbaeza.com) All Rights Reserved.
#                       Pedro M. Baeza <pedro.baeza@serviciosbaeza.com> 
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import sys
import os.path
import urllib2
import xml.sax
import xml.sax.handler
import argparse

class GeoNameXmlHandler(xml.sax.handler.ContentHandler):
    def __init__(self):
        self.__cpNumber = 0
        self.__isTotalResultsCount = 0
        self.__isName = 0
        self.__curCity = ""
        self.isServiceOk = True
        self.message = ""
        self.citys = []
    
    def startElement(self, name, attrs):
        if name == "totalResultsCount":
            self.__isTotalResultsCount = 1
        elif name == "name":
            self.__isName = 1
        elif name == "status":
            self.isServiceOk = False
            self.message = unicode("%s: %s" %(attrs.get("value"), attrs.get("message")))

    def characters(self, ch):
        if self.__isTotalResultsCount == 1:
            self.__cpNumber = int(ch)
        elif self.__isName:
            self.__curCity += ch

    def endElement(self, name):
        if name == "totalResultsCount":
            self.__isTotalResultsCount = 0
        elif name == "name":
            self.citys.append(unicode(self.__curCity))
            self.__curCity = ""
            self.__isName = 0

def filterCity(originalName):
    """
    Pone correctamente la capitalización de palabras como 'De', 'Las', 'Los', 
    cuando son palabras intermedias en el nombre de la ciudad.
    """
    return originalName.replace(' De ', ' de ').replace(' Del ', ' del ').replace(' La ', ' la ').replace(' Las ', ' las ').replace(' El ', ' el ').replace(' Los ', ' los ')

if __name__ == "__main__":
    # Parsear argumentos de la línea de comandos
    argparser = argparse.ArgumentParser(description=u'Descarga los datos de CPs de GeoNames.')
    argparser.add_argument('--start', dest='start', type=int, default=1000, help=u'CP de inicio de la consulta')
    args = argparser.parse_args()
    start = args.start
    # Preparar archivo en el que escribir
    if start == 1000:
        output = open("l10n_es_toponyms_zipcodes.xml", 'w')
        output.write("<?xml version='1.0' encoding='UTF-8'?>\n")
        output.write("<openerp>\n")
        output.write("    <data noupdate='1'>\n")
    else:
        output = open("l10n_es_toponyms_zipcodes.xml", 'a')
    # Iterar por el rango de CPs
    cont = 0
    for cp in range (start, 53000):
        try:
            xml_string = urllib2.urlopen("http://ws.geonames.org/postalCodeSearch?postalcode=%05d&country=ES" %cp).read()
            handler = GeoNameXmlHandler()
            xml.sax.parseString(xml_string, handler)
        except:
            print "Ha ocurrido un error inesperado. Pruebe a lanzar de nuevo el script con el parámetro --start y el número %s." %cp
            sys.exit()            
        if handler.isServiceOk:
            cp_str = "%05d" %cp
            print "%05d: %s" %(cp, handler.citys)
            for city in handler.citys:
                cont += 1
                output.write('        <record id="city_ES_%s" model="city.city">\n' %cont)
                output.write('            <field name="state_id" ref="l10n_es_toponyms.ES%s"/>\n' %cp_str[:2])
                output.write('            <field name="name">%s</field>\n' %filterCity(city).encode('utf-8'))
                output.write('            <field name="zip">%s</field>\n' %cp_str)
                output.write('            <field name="country_id" ref="base.es"/>\n')
                output.write('        </record>\n')
        else:
            print "No se puede continuar la extracción de datos.\n%s\nContinúe después del tiempo indicado utilizando el parámetro --start con el número %s." %(handler.message.encode('utf-8'), cp)
            output.close()
            sys.exit()
    # Se ha terminado ya con todos los códigos postales
    output.write("    </data>\n")
    output.write("</openerp>\n")
    # Cerrar archivo
    output.close()
    print "Proceso terminado"
