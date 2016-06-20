#!/usr/bin/env python
import parser

parse_class = parser.BasKinoParser()

# Parsing categories

recreate = str(input("Re-Drop Existing DB? Y / N [Default - Y] : ")).upper()

if len(recreate) == 0:
    recreate = "Y"

if recreate == "Y":
    parse_class.recreate_tables()
    parse_class.category_parser()

parse_class.get_categories()
