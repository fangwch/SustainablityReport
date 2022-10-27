# coding=utf-8

if __name__ == '__main__':

  import app
  
  from streamlit import bootstrap

  flag_options = {
    'server.port': 8501,
    'global.developmentMode': False,
    'server.enableXsrfProtection': True,
    'server.enableCORS': True
  }

  bootstrap.load_config_options(flag_options)
  
  bootstrap.run(
    app.__file__.replace('.pyc', '.py'), 'streamlit run', [], {}
  )
