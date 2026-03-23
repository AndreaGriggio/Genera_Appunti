import pytinytex

if __name__ == "__main__":
    pytinytex.download_tinytex()
    print(pytinytex.ensure_tinytex_installed())
    print(pytinytex.get_version())

    packages = ["amsmath", "amssymb", "cancel"]

    for pkg in packages:
        pytinytex.install(pkg)
    
    print(pytinytex.list_installed())