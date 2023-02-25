import fastf1

session = fastf1.get_session(2022, 6, 'FP1')
fastf1.Cache.enable_cache('.')
print(f'{session.name = }\n{session.date = }')
