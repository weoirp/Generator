# -*- coding: utf-8 -*-

import os

from clang.cindex import Index
from clang.cindex import Config
from clang.cindex import Cursor
from clang.cindex import CursorKind
from clang.cindex import TokenKind
from clang.cindex import TranslationUnit
from clang.cindex import conf

# 编译需要定义的一些宏
MACRO_DEFS = {
  'WITH_EDITOR': '0',
  'WITH_ENGINE': '1',
  'WITH_UNREAL_DEVELOPER_TOOLS': '0',
  'WITH_PLUGIN_SUPPORT': '1',
  'IS_MONOLITHIC': '0',
  'IS_PROGRAM': '0',
  'UE_BUILD_DEVELOPMENT': '1',
  'UBT_COMPILED_PLATFORM': 'Windows',
  'PLATFORM_WINDOWS': '1',
  'CORE_API': '',
}


class Context(object):
  def __init__(self) -> None:
    self._indent = '  '
    self._depth = 0
    self.all_namespace = {}
    self.all_class = {}
    self.all_struct = {}
    self.all_enum = {}

  def indent(self):
    self._depth += 1

  def unindent(self):
    self._depth -= 1

  def log(self, msg):
    print("{0}{1}".format(self._depth * self._indent, msg))


class Generator(object):
  def __init__(self, options: dict):
    self.index = Index.create()
    self.context = Context()
    self.include_directories = options.get("include_directories", None) or []
    self.macros = options.get("macros", None) or []
    
    self.clang_args = options.get("clang_args", None) or []
    self.clang_options = TranslationUnit.PARSE_INCOMPLETE \
    | TranslationUnit.PARSE_SKIP_FUNCTION_BODIES \
    | TranslationUnit.PARSE_INCLUDE_BRIEF_COMMENTS_IN_CODE_COMPLETION
    
    # 输入的头文件 [{directory: str, headers: []}, ...]
    self.input_headers = options.get("input_headers", None) or []

  def is_from_main_file(self, cursor):
    location = cursor.location
    if location is None:
        return False
    return conf.lib.clang_Location_isFromMainFile(location)
          
  def is_in_system_header(self, cursor):
    location = cursor.location
    if location is None:
        return False
    return conf.lib.clang_Location_isInSystemHeader(location)

  def parse_translation_unit(self, cursor: Cursor):
    self.context.log("translation unit: {}".format(cursor.spelling))
    self._parse_root(cursor)

  def parse_namespace(self, cursor: Cursor):
    self.context.log("namespace: {}".format(cursor.spelling))
    self.context.indent()
    self._parse_root(cursor)
    self.context.unindent()

  def _parse_root(self, cursor: Cursor):
    children = list(cursor.get_children())
    for child in children:
      if self.is_in_system_header(child):
        continue
      if child.kind == CursorKind.NAMESPACE:
        self.parse_namespace(child)
      elif child.kind in (CursorKind.CLASS_DECL, CursorKind.STRUCT_DECL):
        self.parse_class(child)
      elif child.kind in (CursorKind.ENUM_DECL, CursorKind.ENUM_CONSTANT_DECL):
        self.parse_enum(child)
      elif child.kind == CursorKind.VAR_DECL:
        self.parse_variable(child)
      elif child.kind == CursorKind.FUNCTION_DECL:
        self.parse_function(child)
      # elif child.kind == CursorKind.CLASS_TEMPLATE:
      #   self.parse_template_class(child)
      # elif child.kind == CursorKind.FUNCTION_TEMPLATE:
      #   self.parse_template_function(child) 
      else:
        self.context.log("unknown {}".format(cursor.kind))     


  def parse_class(self, cursor: Cursor, inner_class=False):
    if inner_class:
      self.context.log("inner class: {}".format(cursor.spelling))
    else:
      self.context.log("class: {}".format(cursor.spelling))
    self.context.indent()
    class_type = cursor.type.spelling
    self.context.log("type: {}".format(class_type))
    if inner_class:
      self.context.unindent()
      return
    children = list(cursor.get_children())
    for child in children:
      if self.is_in_system_header(child):
        continue
      if child.kind == CursorKind.CXX_BASE_SPECIFIER:
        base_class_type = child.type.spelling
        access_name = child.access_specifier.name
        self.context.log("inhert: {} {}".format(access_name, base_class_type))
      elif child.kind == CursorKind.CXX_METHOD:
        self.parse_cxxmethod(child)
      elif child.kind in (CursorKind.FIELD_DECL, CursorKind.VAR_DECL):
        self.parse_field(child)
      elif child.kind in (CursorKind.CLASS_DECL, CursorKind.STRUCT_DECL):
        self.parse_class(child, True)

    self.context.unindent()

  def parse_enum(self, cursor: Cursor):
    self.context.log("enum: {}".format(cursor.spelling))
    self.context.indent()
    enum_type = cursor.type.spelling
    self.context.log("type: {}".format(enum_type))
    children = list(cursor.get_children())
    for child in children:
      if child.kind == CursorKind.ENUM_CONSTANT_DECL:
        self.parse_enum_constant(child)
    self.context.unindent()

  def parse_variable(self, cursor: Cursor):
    self.context.log("variable: {}".format(cursor.spelling))
    self.context.indent()
    self._parse_var(cursor)
    self.context.unindent()

  def parse_function(self, cursor: Cursor):
    self.context.log("function: {}".format(cursor.spelling))
    self.context.indent()
    self._parse_method(cursor)
    self.context.unindent()

  def parse_param(self, cursor: Cursor):
    self.context.log("param: {}".format(cursor.spelling))
    self.context.indent()
    param_type = cursor.type.spelling
    default_value = None
    tokens = list(cursor.get_tokens())
    for i, token in enumerate(tokens):
      if token.kind == TokenKind.PUNCTUATION and token.spelling == "=" and i+1 < len(tokens):
        default_value = tokens[i+1].spelling
        break
    self.context.log("type: {}".format(param_type))
    if default_value is not None:
      self.context.log("default: {}".format(default_value))
    self.context.unindent()

  def parse_cxxmethod(self, cursor: Cursor):
    self.context.log("cxxmethod: {}".format(cursor.spelling))
    self.context.indent()
    access_name = cursor.access_specifier.name
    self.context.log("access: {}".format(access_name))
    self._parse_method(cursor)
    self.context.unindent()
  
  def _parse_method(self, cursor: Cursor):
    self.context.log("return: {}".format(cursor.result_type.spelling))
    self.context.log("storage: {}".format(cursor.storage_class.name))
    children = list(cursor.get_children())
    for child in children:
      if self.is_in_system_header(child):
        continue
      if child.kind == CursorKind.PARM_DECL:
        self.parse_param(child)
    
  def parse_field(self, cursor: Cursor):
    self.context.log("field: {}".format(cursor.spelling))
    self.context.indent()
    access_name = cursor.access_specifier.name
    self.context.log("access: {}".format(access_name))
    self._parse_var(cursor)
    self.context.unindent()
    
  def _parse_var(self, cursor: Cursor):
    variable_type = cursor.type.spelling
    storage_class_name = cursor.storage_class.name    
    children = list(cursor.get_children())
    init_cursor = children[0] if len(children) > 0 else None
    if init_cursor is not None and init_cursor.kind == CursorKind.LAMBDA_EXPR:
      variable_type = "lambda"
    self.context.log("type: {}".format(variable_type))
    self.context.log("storage: {}".format(storage_class_name))
      

  def parse_enum_constant(self, cursor: Cursor):
    self.context.log("field: {}".format(cursor.spelling))
    self.context.indent()
    self.context.log("type: {}".format(cursor.type.spelling))
    self.context.log("value: {}".format(cursor.enum_value))
    self.context.unindent()
    
  def parse_template_class(self, cursor: Cursor):
    self.context.log("template class: {}".format(cursor.spelling))

  def parse_template_function(self, cursor: Cursor):
    self.context.log("template function: {}".format(cursor.spelling))

  def parse(self):
    input_file = "input.h"
    include_directories = []
    outputs = []
    for item in self.input_headers:
      include_directories.append(os.path.realpath(item["directory"]))
      outputs += ["#include \"{}\"".format(header) for header in item["headers"]]
    
    if len(outputs) == 0:
      return
    
    with open(input_file, "w") as f:
      f.write("\n".join(outputs))

    include_directories = list(set(include_directories))
    clang_args = self.clang_args + \
      ["-I" + path for path in self.include_directories] + \
      ["-I" + path for path in include_directories] + \
      ["-D" + macro for macro in self.macros]
    
    # parse an entire translation unit
    tu = self.index.parse(input_file, args=clang_args, options=self.clang_options)
    self.parse_translation_unit(tu.cursor)



# todo: package 对应的路径，头文件
def find_package_headers(directory):
  '''
    找出 Public/ 下的 .h, .hpp
  '''
  headers = []
  ignores = [".svn", ".git"]
  public_directory = os.path.join(directory, "Public")
  for root, dirs, files in os.walk(public_directory):
    for ignore in ignores:
      if ignore in dirs:
        dirs.remove(ignore)
    for file in files:
      if file.endswith(".h") or file.endswith(".hpp"):
        path = os.path.relpath(os.path.join(root, file), public_directory)
        headers.append(path)
  return headers


def main():
  clang_lib_path = os.path.join(os.path.dirname(__file__), "libclang")
  Config.set_library_path(clang_lib_path)

  # generator = Generator({
  #   "clang_args": ["-x", "c++", "-std=c++17", "-Wno-everything"],
  #   "macros": ["VECTORVM_API"],
  #   "input_headers": [
  #     {
  #       "directory": "./",
  #       "headers": ["macros.h", "test.cpp"]
  #     },
  #   ]
  # })

  VectorVM_package = os.path.realpath("D:/repositories/UnrealEngine-5.2.0-release/Engine/Source/Runtime/VectorVM")
  VectorVM_headers = find_package_headers(VectorVM_package)
  generator = Generator({
    "clang_args": ["-x", "c++", "-std=c++17", "-Wno-everything"],
    "macros": ["VECTORVM_API"],
    "input_headers": [
      {
        "directory": "./",
        "headers": ["macros.h"],
      },
      {
        "directory": os.path.join(VectorVM_package, "Public"),
        "headers": VectorVM_headers,
      },
    ]
  })

  generator.parse()


if __name__ == '__main__':
  main()