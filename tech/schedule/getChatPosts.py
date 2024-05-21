from constants import FONT_L, FONT_S
from bot import dp, bot, cursor, db
import random
from random import randint
from PIL import ImageFilter
from io import BytesIO
from datetime import datetime
import pytz
import textwrap
import asyncio
import numpy as np
import keyboard as kb
from aiogram import types
from other.phrases import get_random_phrases
from aiogram.dispatcher.filters import IDFilter
from constants import ADMIN_ID, CHANNEL_ID
from handlers.astrology.getMoon import get_moon_today
