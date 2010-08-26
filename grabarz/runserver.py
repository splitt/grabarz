from grabarz import app
from grabarz import config

if __name__ == '__main__':
    with open("__instance__.txt") as f:
        instance = f.read()
                
    app.config.from_object('config.%sConfig' % instance.capitalize())
    app.run()