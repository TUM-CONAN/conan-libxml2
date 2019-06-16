#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import shutil
from conans import CMake, ConanFile, AutoToolsBuildEnvironment, tools

class LibxmlConan(ConanFile):
    name = "libxml2"
    package_revision = "-r2"
    upstream_version = "2.9.8"
    version = "{0}{1}".format(upstream_version, package_revision)
    generators = "cmake"
    settings =  "os", "compiler", "arch", "build_type"
    options = {"shared": [True, False]}
    default_options = "shared=True"
    exports = [
        "patches/CMakeLists.txt",
        "patches/CMakeProjectWrapper.txt",
        "patches/FindIconv.cmake",
        "patches/FindLibXml2.cmake",
        "patches/xmlversion.h.patch"
    ]
    url = "https://git.ircad.fr/conan/conan-libxml2"
    source_subfolder = "source_subfolder"
    build_subfolder = "build_subfolder"

    def configure(self):
        del self.settings.compiler.libcxx
        if 'CI' not in os.environ:
            os.environ["CONAN_SYSREQUIRES_MODE"] = "verify"

    def requirements(self):
        self.requires("common/1.0.0@sight/stable")
        if tools.os_info.is_windows:
            self.requires("zlib/1.2.11-r2@sight/testing")
            self.requires("winiconv/0.0.8-r2@sight/testing")

    def build_requirements(self):
        if tools.os_info.is_linux:
            pack_names = [
                "libiconv-hook-dev",
                "zlib1g-dev"
            ]
            installer = tools.SystemPackageTool()
            for p in pack_names:
                installer.install(p)

    def system_requirements(self):
        if tools.os_info.is_linux:
            pack_names = [
                "libiconv-hook1",
                "zlib1g"
            ]
            installer = tools.SystemPackageTool()
            for p in pack_names:
                installer.install(p)

    def source(self):
        tools.get("http://xmlsoft.org/sources/libxml2-{0}.tar.gz".format(self.upstream_version))
        os.rename("libxml2-{0}".format(self.upstream_version), self.source_subfolder)

    def configure(self):
        del self.settings.compiler.libcxx
        if self.settings.os == "Windows" and not self.options.shared:
            self.output.warn("Warning! Static builds in Windows are unstable")

    def build(self):
        # Import common flags and defines
        import common

        if self.settings.os == "Windows":
            libxml2_source_dir = os.path.join(self.source_folder, self.source_subfolder)
            shutil.move("patches/CMakeProjectWrapper.txt", "CMakeLists.txt")
            shutil.move("patches/CMakeLists.txt", "%s/CMakeLists.txt" % libxml2_source_dir)
            shutil.move("patches/FindIconv.cmake", "%s/FindIconv.cmake" % libxml2_source_dir)
            tools.patch(libxml2_source_dir, "patches/xmlversion.h.patch")

            cmake = CMake(self)
            
            # Set common flags
            cmake.definitions["SIGHT_CMAKE_C_FLAGS"] = common.get_c_flags() + " /TC "
            cmake.definitions["SIGHT_CMAKE_CXX_FLAGS"] = common.get_cxx_flags()
            
            cmake.configure(build_folder=self.build_subfolder)
            cmake.build()
            cmake.install()
        else:
            env_build = AutoToolsBuildEnvironment(self)
            env_build.fpic = True

            with tools.environment_append(env_build.vars):
                with tools.environment_append({
                    "CFLAGS": common.get_full_c_flags(build_type=self.settings.build_type),
                    "CXXFLAGS": common.get_full_cxx_flags(build_type=self.settings.build_type)
                }):
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
        self.copy("FindLibXml2.cmake", src="patches", dst=".", keep_path=False)

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
        if self.settings.os == "Linux" or self.settings.os == "Macos":
            self.cpp_info.libs.append('m')
   
