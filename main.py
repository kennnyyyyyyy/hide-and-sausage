# =============================================================================
#  HIDE & SAUSAGE - 5FTC2067 Artificial Intelligence Principles Mini Project
#  Student Name : Kenzo Jonathan Harapan Ji      Student ID : 4234QLMV
#
#  main.py - run this to start the game:   python main.py
# =============================================================================

from hide_and_sausage.ui.app import App
from hide_and_sausage.ui.scenes_menu import TitleScene


# -----------------------------------------------------------------------------
# main - opens the game window and starts on the title screen.
#   (no parameters)
# -----------------------------------------------------------------------------
def main():
    app = App()
    app.run(TitleScene(app))


if __name__ == "__main__":
    main()
