#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import shutil
from conans import CMake, ConanFile, tools

class LibxmlConan(ConanFile):
    name = "libxml2"
    version = "2.9.8"
    generators = "cmake"
    settings =  "os", "compiler", "arch", "build_type"
    options = {"shared": [True, False], "fPIC": [True, False]}
    default_options = "shared=True", "fPIC=True"
    exports = [
        "patchs/CMakeLists.txt",
        "patchs/CMakeProjectWrapper.txt",
        "patchs/config.linux.h",
        "patchs/config.osx.h",
        "patchs/FindIconv.cmake"
    ]
    url = "https://gitlab.lan.local/conan/conan-libxml2"
    source_subfolder = "source_subfolder"
    build_subfolder = "build_subfolder"

    def requirements(self):
        self.requires("zlib/1.2.11@fw4spl/stable")
        if tools.os_info.is_windows:
            self.requires("winiconv/0.0.8@fw4spl/stable")

    def system_requirements(self):
        if tools.os_info.is_linux:
            pack_names = ["libiconv-hook-dev"]

            if self.settings.arch == "x86":
                pack_names = [item+":i386" for item in pack_names]

            installer = tools.SystemPackageTool()
            installer.update() # Update the package database
            installer.install(" ".join(pack_names)) # Install the package

    def source(self):
        tools.get("http://xmlsoft.org/sources/libxml2-{0}.tar.gz".format(self.version))
        os.rename("libxml2-{0}".format(self.version), self.source_subfolder)
        
    def config_options(self):
        if tools.os_info.is_windows:
            del self.options.fPIC

    def configure(self):
        self.requires("zlib/1.2.11@fw4spl/stable")
        if tools.os_info.is_windows:
            self.requires("winiconv/0.0.8@fw4spl/stable")
        del self.settings.compiler.libcxx
        if self.settings.os == "Windows" and not self.options.shared:
            self.output.warn("Warning! Static builds in Windows are unstable")

    def build(self):
        libxml2_source_dir = os.path.join(self.source_folder, self.source_subfolder)
        shutil.move("patchs/CMakeProjectWrapper.txt", "CMakeLists.txt")
        shutil.move("patchs/CMakeLists.txt", "%s/CMakeLists.txt" % libxml2_source_dir)
        shutil.move("patchs/config.linux.h", "%s/config.linux.h" % libxml2_source_dir)
        shutil.move("patchs/config.osx.h", "%s/config.osx.h" % libxml2_source_dir)
        shutil.move("patchs/FindIconv.cmake", "%s/FindIconv.cmake" % libxml2_source_dir)
        cmake = CMake(self)
        cmake.configure(build_folder=self.build_subfolder)
        cmake.build()
        cmake.install()

    def package(self):
        self.copy("FindLibXml2.cmake", ".", ".")

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
        if self.settings.os == "Linux" or self.settings.os == "Macos":
            self.cpp_info.libs.append('m')
   
