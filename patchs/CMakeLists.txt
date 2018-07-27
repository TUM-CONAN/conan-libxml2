cmake_minimum_required(VERSION 3.5)

project(libxml2 C)

option(INSTALL_HEADERS "Install public header files" ON)

set(CMAKE_SHARED_LIBRARY_PREFIX)
set(CMAKE_STATIC_LIBRARY_PREFIX)

if(${CMAKE_VERSION} VERSION_LESS "3.11.0")
    message(STATUS "Using custom CMake find_package to find lib Iconv") 
    list(APPEND CMAKE_MODULE_PATH ${CMAKE_CURRENT_LIST_DIR})
endif()

find_package(ZLIB REQUIRED)
find_package(Iconv REQUIRED)

file(GLOB SOURCES *.c)
list(FILTER SOURCES EXCLUDE REGEX "/(run|test|trio)[^/]*$")
list(FILTER SOURCES EXCLUDE REGEX "xml(lint|catalog).c$")

# Generate xmlexports with fixed definition of LIBXML_STATIC
file(READ include/libxml/xmlexports.h XMLEXPORTS_H)
if(BUILD_SHARED_LIBS)
    string(REPLACE "!defined(LIBXML_STATIC)" "1" XMLEXPORTS_H "${XMLEXPORTS_H}")
else()
    string(REPLACE "!defined(LIBXML_STATIC)" "0" XMLEXPORTS_H "${XMLEXPORTS_H}")
endif()
file(WRITE ${CMAKE_CURRENT_BINARY_DIR}/xmlexports.h "${XMLEXPORTS_H}")

if(CMAKE_SYSTEM_NAME STREQUAL "Windows")
    configure_file(include/win32config.h config.h COPYONLY)
elseif(CMAKE_SYSTEM_NAME STREQUAL "Darwin")
    configure_file("config.osx.h" config.h COPYONLY)
elseif(CMAKE_SYSTEM_NAME STREQUAL "Linux")
    configure_file("config.linux.h" config.h COPYONLY)
else()
    message(FATAL_ERROR "No config.h checked in for the target platform. Please run ./configure for libxml2 and add the resulting config.h into this port.")
endif()

add_library(libxml2 ${SOURCES})
if(INSTALL_HEADERS)
    file(GLOB PUBLIC_HEADERS include/libxml/*.h)
    list(FILTER PUBLIC_HEADERS EXCLUDE REGEX "xmlexports\\.h$")
    list(APPEND PUBLIC_HEADERS ${CMAKE_CURRENT_BINARY_DIR}/xmlexports.h)

    set_target_properties(libxml2 PROPERTIES PUBLIC_HEADER "${PUBLIC_HEADERS}")
endif()

target_include_directories(libxml2 PRIVATE ${CMAKE_CURRENT_BINARY_DIR} include 
    ${ZLIB_INCLUDE_DIRS}
    ${Iconv_INCLUDE_DIR}
)
target_link_libraries(libxml2 PRIVATE
    ${ZLIB_LIBRARIES}
    ${Iconv_LIBRARY}
)
if(CMAKE_SYSTEM_NAME STREQUAL "Windows")
    target_include_directories(libxml2 PRIVATE win32/vc10)
    target_link_libraries(libxml2 PRIVATE
        wsock32.lib
        ws2_32.lib
    )
    target_compile_definitions(libxml2 PRIVATE
        -DHAVE_WIN32_THREADS
    )
endif()

target_compile_definitions(libxml2 PRIVATE
    -D_CRT_SECURE_NO_DEPRECATE
    -D_CRT_NONSTDC_NO_DEPRECATE
    -D_REENTRANT
    -DNOLIBTOOL
    -DHAVE_ZLIB_H
)
if(NOT BUILD_SHARED_LIBS)
    target_compile_definitions(libxml2 PRIVATE -DLIBXML_STATIC)
endif()

set(TARGET_INSTALL_OPTIONS)
if(INSTALL_HEADERS)
    set(TARGET_INSTALL_OPTIONS PUBLIC_HEADER DESTINATION include/libxml)
endif()

install(TARGETS libxml2
    RUNTIME DESTINATION bin
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
    ${TARGET_INSTALL_OPTIONS}
)
