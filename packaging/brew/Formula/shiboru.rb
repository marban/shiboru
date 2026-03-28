class Shiboru < Formula
  include Language::Python::Virtualenv

  desc "macOS command-line image optimizer for PNG, JPEG, GIF, SVG, and ICO"
  homepage "https://github.com/marban/shiboru"
  url "https://github.com/marban/shiboru/archive/refs/tags/v1.0.0.tar.gz"
  sha256 "280cff2a2e718e4a28fc05ec57da73e5f86bbd000926846ce9b46d656cdd5b2c"
  license "MIT"

  depends_on "python@3.13"
  depends_on "oxipng"
  depends_on "jpegoptim"
  depends_on "gifsicle"

  resource "scour" do
    url "https://files.pythonhosted.org/packages/75/19/f519ef8aa2f379935a44212c5744e2b3a46173bf04e0110fb7f4af4028c9/scour-0.38.2.tar.gz"
    sha256 "6881ec26660c130c5ecd996ac6f6b03939dd574198f50773f2508b81a68e0daf"
  end

  def install
    virtualenv_install_with_resources
  end

  test do
    system bin/"shiboru", "--version"
    system bin/"shiboru", "--help"
  end
end
