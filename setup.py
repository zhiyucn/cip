from cx_Freeze import setup, Executable

setup(
    name="cip",
    version="0.0.2",
    description="cip - Better then pip.",
    executables=[Executable("cip.py")]
)
