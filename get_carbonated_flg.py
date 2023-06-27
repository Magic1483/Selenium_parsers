import re
def get_carbonated_flg(water_type):
    carbs =  ""
    water_type = water_type.replace("\xa0", " ").replace(" ","").lower()
    index = re.search("азиров",water_type) 
    if index:
      if re.search("егазир",water_type):
         carbs = 'Негазированная'    
      else:
         carbs = 'Газированная'    
    else:
       carbs =  "" 
     
    return carbs