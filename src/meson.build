pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
moduledir = join_paths(pkgdatadir, 'gnome_todo')
ttd_core_dir = join_paths(pkgdatadir, 'ttd_core')
devtoolsdir = join_paths(pkgdatadir, 'devtools')
fs = import('fs')

# Blueprint compilation
blueprints = custom_target('blueprints',
  input: files(
    'ui/window.blp',
    'ui/add_task_dialog.blp',
    'ui/welcome_dialog.blp',
    'ui/preferences_dialog.blp',
    'ui/content_header.blp',
    'ui/task_row.blp',
    'ui/task_detail_panel.blp',
    'ui/smart_filter_row.blp',
  ),
  output: '.',
  command: [
    find_program('blueprint-compiler'),
    'batch-compile',
    '@OUTPUT@',
    '@CURRENT_SOURCE_DIR@',
    '@INPUT@',
  ],
)

# GResource bundle
gnome.compile_resources('gnome-todo',
  'dev.bayhan.GnomeTodo.gresource.xml',
  gresource_bundle: true,
  install: true,
  install_dir: pkgdatadir,
  dependencies: blueprints,
)

# Launcher script
conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').full_path())
conf.set('pkgdatadir', pkgdatadir)

configure_file(
  input: 'gnome-todo.in',
  output: 'gnome-todo',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir'),
  install_mode: 'rwxr-xr-x',
)

configure_file(
  input: 'gnome-todo-panel.in',
  output: 'gnome-todo-panel',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir'),
  install_mode: 'rwxr-xr-x',
)

# Install gnome_todo Python package
gui_sources = [
  'gnome_todo/__init__.py',
  'gnome_todo/app.py',
  'gnome_todo/_config.py',
  'gnome_todo/_content.py',
  'gnome_todo/_content_header.py',
  'gnome_todo/_core.py',
  'gnome_todo/_detail_panel.py',
  'gnome_todo/_detail_panel_tags.py',
  'gnome_todo/_dialogs.py',
  'gnome_todo/_file_monitor.py',
  'gnome_todo/_preferences.py',
  'gnome_todo/_shortcuts.py',
  'gnome_todo/_sidebar.py',
  'gnome_todo/_sidebar_state.py',
  'gnome_todo/_task_row_state.py',
  'gnome_todo/_ui.py',
  'gnome_todo/_task_row.py',
  'gnome_todo/_welcome.py',
  'gnome_todo/_widgets.py',
  'gnome_todo/_window.py',
  'gnome_todo/_window_state.py',
  'gnome_todo/panel_cli.py',
]
install_data(gui_sources, install_dir: moduledir)

devtools_root = join_paths(meson.project_source_root(), 'devtools')
if fs.exists(join_paths(devtools_root, 'screenshot.py'))
  devtools_sources = [
    join_paths(devtools_root, '__init__.py'),
    join_paths(devtools_root, 'screenshot.py'),
  ]
  install_data(devtools_sources, install_dir: devtoolsdir)
endif

# ── ttd_core: Rust native library ─────────────────────────────────────

cargo = find_program('cargo', required: false)
if cargo.found()
  ttd_core_cargo_toml = join_paths(
    meson.project_source_root(), 'vendor', 'ttd-core', 'Cargo.toml',
  )
  ttd_core_target_dir = join_paths(meson.project_build_root(), 'ttd-core-target')
  ttd_core_built_lib = join_paths(ttd_core_target_dir, 'release', 'libttd_core.so')

  custom_target('ttd-core-native',
    output: 'libttd_core.so',
    command: [
      'sh', '-c',
      '@0@ build --release --manifest-path @1@ --target-dir @2@ && cp @3@ @OUTPUT0@'.format(
        cargo.full_path(),
        ttd_core_cargo_toml,
        ttd_core_target_dir,
        ttd_core_built_lib,
      ),
    ],
    install: true,
    install_dir: pkgdatadir,
    build_by_default: true,
  )
endif

# ── ttd_core: Python FFI bridge and package ───────────────────────────

ttd_core_bindings_dir = join_paths(
  meson.project_source_root(), 'vendor', 'ttd-core', 'bindings', 'python',
)

install_data(
  join_paths(ttd_core_bindings_dir, '_ttd_core.py'),
  install_dir: pkgdatadir,
)

ttd_core_sources = [
  join_paths(ttd_core_bindings_dir, 'ttd_core', '__init__.py'),
  join_paths(ttd_core_bindings_dir, 'ttd_core', '_compat.py'),
  join_paths(ttd_core_bindings_dir, 'ttd_core', 'env.py'),
  join_paths(ttd_core_bindings_dir, 'ttd_core', 'filtering.py'),
  join_paths(ttd_core_bindings_dir, 'ttd_core', 'grouping.py'),
  join_paths(ttd_core_bindings_dir, 'ttd_core', 'mutations.py'),
  join_paths(ttd_core_bindings_dir, 'ttd_core', 'operations.py'),
  join_paths(ttd_core_bindings_dir, 'ttd_core', 'parser.py'),
  join_paths(ttd_core_bindings_dir, 'ttd_core', 'task.py'),
  join_paths(ttd_core_bindings_dir, 'ttd_core', 'text_editing.py'),
  join_paths(ttd_core_bindings_dir, 'ttd_core', 'todo_directory.py'),
  join_paths(ttd_core_bindings_dir, 'ttd_core', 'todo_file.py'),
]
install_data(ttd_core_sources, install_dir: ttd_core_dir)
