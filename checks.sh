#!/bin/bash

black .

pytest

pip freeze > requirements.txt
