from kivy.app import App
from kivy.uix.widget import Widget

class Skate(Widget):
    pass

class SkateApp(App):
    def build(self):
        return Skate()
    
if __name__ == '__main__':   
    SkateApp().run()