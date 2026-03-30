class Shiboru < Formula
  include Language::Python::Virtualenv

  desc "Opinionated macOS command-line image optimizer for PNG, JPEG, GIF, SVG, and ICO"
  homepage "https://github.com/marban/shiboru"
  url "https://github.com/marban/shiboru/archive/refs/tags/v1.0.6.tar.gz"
  sha256 "00459223260554925e0971ae130d5b8816f4a6085547169e2cd382812a681f39"
  license "MIT"

  depends_on "python@3.13"
  depends_on "oxipng"
  depends_on "jpegoptim"
  depends_on "gifsicle"

  resource "scour" do
    url "https://files.pythonhosted.org/packages/75/19/f519ef8aa2f379935a44212c5744e2b3a46173bf04e0110fb7f4af4028c9/scour-0.38.2.tar.gz"
    sha256 "6881ec26660c130c5ecd996ac6f6b03939dd574198f50773f2508b81a68e0daf"
  end

  resource "six" do
    url "https://files.pythonhosted.org/packages/94/e7/b2c673351809dca68a0e064b6af791aa332cf192da575fd474ed7d6f16a2/six-1.17.0.tar.gz"
    sha256 "ff70335d468e7eb6ec65b95b99d3a2836546063f63acc5171de367e834932a81"
  end

  def install
    virtualenv_install_with_resources
  end

  test do
    (testpath/"icon.svg").write <<~SVG
      <?xml version="1.0" encoding="UTF-8"?>
      <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32">
        <metadata>formula runtime test</metadata>
        <circle cx="16" cy="16" r="12" fill="#000"/>
      </svg>
    SVG

    system bin/"shiboru", "--version"
    system bin/"shiboru", "--help"
    system bin/"shiboru", "icon.svg"
    assert_predicate testpath/"icon-optimized.svg", :exist?
  end
end
