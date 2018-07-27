#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import shutil
from conans import CMake, ConanFile, AutoToolsBuildEnvironment, tools

class LibxmlConan(ConanFile):
    name = "libxml2"
    version = "2.9.8"
    generators = "cmake"
    settings =  "os", "compiler", "arch", "build_type"
    options = {"shared": [True, False], "fPIC": [True, False]}
    default_options = "shared=True", "fPIC=True"
    exports = [
        "patches/CMakeLists.txt",
        "patches/CMakeProjectWrapper.txt",
        "patches/FindIconv.cmake",
        "patches/xmlversion.h.patch"
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
        del self.settings.compiler.libcxx
        if self.settings.os == "Windows" and not self.options.shared:
            self.output.warn("Warning! Static builds in Windows are unstable")

    def build(self):
        if self.settings.os == "Windows":
            libxml2_source_dir = os.path.join(self.source_folder, self.source_subfolder)
            shutil.move("patches/CMakeProjectWrapper.txt", "CMakeLists.txt")
            shutil.move("patches/CMakeLists.txt", "%s/CMakeLists.txt" % libxml2_source_dir)
            shutil.move("patches/FindIconv.cmake", "%s/FindIconv.cmake" % libxml2_source_dir)
            tools.patch(libxml2_source_dir, "patches/xmlversion.h.patch")
            cmake = CMake(self)
            cmake.configure(build_folder=self.build_subfolder)
            cmake.build()
            cmake.install()
        else:
            env_build = AutoToolsBuildEnvironment(self)
            env_build.fpic = self.options.fPIC
            with tools.environment_append(env_build.vars):
                with tools.chdir(self.source_subfolder):
                    # fix rpath
                    if self.settings.os == "Macos":
                        tools.replace_in_file("configure", r"-install_name \$rpath/", "-install_name ")
                    configure_args = ['--with-python=no', '--without-lzma']
                    if self.options.shared:
                        configure_args.extend(['--enable-shared', '--disable-static'])
                    else:
                        configure_args.extend(['--enable-static', '--disable-shared'])
                    env_build.configure(args=configure_args)
                    env_build.make()
                    env_build.install()

    def package(self):
        self.copy("FindLibXml2.cmake", ".", ".")

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
        if self.settings.os == "Linux" or self.settings.os == "Macos":
            self.cpp_info.libs.append('m')
   
