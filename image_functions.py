import streamlit as st


def classify_aqi(aqi):
    if aqi >= 0 and aqi <= 50:
        return ("Good", "00e400", aqi / 50)
    elif aqi >= 51 and aqi <= 100:
        return ("Moderate", "ffff00", aqi / 50)
    elif aqi >= 101 and aqi <= 150:
        return ("Unhealthy for sensitive groups", "ff7e00", aqi / 50)
    elif aqi >= 151 and aqi <= 200:
        return ("Unhealthy", "ff0000", aqi / 50)
    elif aqi >= 201 and aqi <= 300:
        return ("Very Unhealthy", "8f3f97", aqi / 100)
    elif aqi >= 301 and aqi <= 500:
        return ("Hazardous", "7e0023", aqi / 200)


def example(color1, color2, color3, aqi):
    st.markdown(
        f'<p style="text-align:center;background-color: linear-gradient(to right,{color1}, {color2});color:{color3};font-size:24px;border-radius:2%;">{st.header(aqi)}</p>',
        unsafe_allow_html=True,
    )


def widget(aqi_category, aqi_number, aqi, city_name):
    city = city_name.capitalize() + " Air Quality"
    st.title(city)
    aqi_category = aqi_category.capitalize()
    st.markdown(
        f'<p style="text-align:justify;background-color:#{aqi_number};background-size:300px 150px;color:black;font-size:32px;border-radius:2%;margin-bottom:-1em;margin-top:0em;">{aqi_category } with AQI of {aqi}</p>',
        unsafe_allow_html=True,
    )
    #html = """
    #<script  type="text/javascript"  charset="utf-8">  
    #    (function(w,d,t,f){  w[f]=w[f]||function(c,k,n){s=w[f],k=s['k']=(s['k']||(k?('&k='+k):''));s['c']=  
    #    c=(c  instanceof  Array)?c:[c];s['n']=n=n||0;L=d.createElement(t),e=d.getElementsByTagName(t)[0];  
    #    L.async=1;L.src='//feed.aqicn.org/feed/'+(c[n].city)+'/'+(c[n].lang||'')+'/feed.v1.js?n='+n+k;  
    #    e.parentNode.insertBefore(L,e);  };  })(  window,document,'script','_aqiFeed'  );    
    #</script>
    #<span  id="city-aqi-container"></span>  
 # 
  #  <script  type="text/javascript"  charset="utf-8">  
   #     _aqiFeed({  
    #                display: "%details",
     #               container:"city-aqi-container",
     #              city:"CITY_NAME"  });  
    #</script>
#""".replace(
#        "CITY_NAME", city_name
#    )
#    st.components.v1.html(html=html, width=250, height=250)


def hex_to_rgb(hex):
    rgb = []
    for i in (0, 2, 4):
        decimal = int(hex[i : i + 2], 16)
        rgb.append(decimal)

    return tuple(rgb)
