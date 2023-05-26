from setuptools import setup

setup(
    name="paralelismo_examen",
    version="0.1.0",
    description="Preguntas respondidas del 1 al 3",
    author="Juan Perlas",
    author_email="juanarroyoperlas@gmail.com",
    url="https://github.com/Juanperlas/paralelismo_examen",
    install_requires=[
        "flask",
        "platform",
        "psutil",
        "re",
        "subprocess",
        "cpuinfo",
        "pynvml",
        "pandas",
        "pythoncom",
        "wmi",
        "winreg",
    ],
)
