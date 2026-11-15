// Native GDevelop validator + HTML5 exporter for CRACKLINE.
// Loads game.json with GDevelop's own GDCore/GDJS (built from source), checks every
// instruction against the real extension metadata, then runs the official HTML5 exporter.
#include <dlfcn.h>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <sstream>
#include "GDCore/IDE/AbstractFileSystem.h"
#include "GDCore/IDE/PlatformManager.h"
#include "GDCore/Project/Project.h"
#include "GDCore/Project/Layout.h"
#include "GDCore/Project/ExternalEvents.h"
#include "GDCore/Project/ExternalLayout.h"
#include "GDCore/Serialization/Serializer.h"
#include "GDCore/Events/Event.h"
#include "GDCore/Events/EventsList.h"
#include "GDCore/Events/Instruction.h"
#include "GDCore/Events/InstructionsList.h"
#include "GDCore/Extensions/Metadata/MetadataProvider.h"
#include "GDCore/Extensions/Metadata/InstructionMetadata.h"
#include "GDCore/Extensions/PlatformExtension.h"
#include "GDCore/Events/CodeGeneration/DiagnosticReport.h"
#include "GDJS/Extensions/JsPlatform.h"
#include "GDJS/IDE/Exporter.h"
#include "GDJS/IDE/ExporterHelper.h"
namespace fs = std::filesystem;

class NativeFS : public gd::AbstractFileSystem {
 public:
  void MkDir(const gd::String& p) override { fs::create_directories(p.ToLocale()); }
  bool DirExists(const gd::String& p) override { return fs::is_directory(p.ToLocale()); }
  bool FileExists(const gd::String& p) override { return fs::is_regular_file(p.ToLocale()); }
  bool ClearDir(const gd::String& p) override {
    if (!fs::exists(p.ToLocale())) return true;
    for (auto& e : fs::directory_iterator(p.ToLocale())) fs::remove_all(e.path());
    return true;
  }
  gd::String GetTempDir() override { return "/tmp/gdexport_tmp"; }
  gd::String FileNameFrom(const gd::String& f) override { return gd::String::FromUTF8(fs::path(f.ToLocale()).filename().string()); }
  gd::String DirNameFrom(const gd::String& f) override { return gd::String::FromUTF8(fs::path(f.ToLocale()).parent_path().string()); }
  bool MakeAbsolute(gd::String& f, const gd::String& base) override {
    if (IsAbsolute(f)) return true;
    f = gd::String::FromUTF8((fs::path(base.ToLocale()) / f.ToLocale()).lexically_normal().string()); return true;
  }
  bool IsAbsolute(const gd::String& f) override { return fs::path(f.ToLocale()).is_absolute(); }
  bool MakeRelative(gd::String& f, const gd::String& base) override {
    f = gd::String::FromUTF8(fs::path(f.ToLocale()).lexically_relative(base.ToLocale()).string()); return true;
  }
  bool CopyFile(const gd::String& a, const gd::String& b) override {
    std::error_code ec; fs::create_directories(fs::path(b.ToLocale()).parent_path(), ec);
    fs::copy_file(a.ToLocale(), b.ToLocale(), fs::copy_options::overwrite_existing, ec);
    if (ec) std::cerr << "COPY FAIL " << a << " -> " << b << ": " << ec.message() << "\n";
    return !ec;
  }
  bool WriteToFile(const gd::String& f, const gd::String& c) override {
    std::error_code ec; fs::create_directories(fs::path(f.ToLocale()).parent_path(), ec);
    std::ofstream o(f.ToLocale()); o << c.Raw(); return true;
  }
  gd::String ReadFile(const gd::String& f) override {
    std::ifstream i(f.ToLocale()); std::stringstream s; s << i.rdbuf(); return gd::String::FromUTF8(s.str());
  }
  std::vector<gd::String> ReadDir(const gd::String& p, const gd::String& ext) override {
    std::vector<gd::String> r;
    if (!fs::exists(p.ToLocale())) return r;
    for (auto& e : fs::directory_iterator(p.ToLocale()))
      if (ext.empty() || e.path().extension().string() == ext.ToLocale()) r.push_back(gd::String::FromUTF8(e.path().string()));
    return r;
  }
};

int problems = 0;
std::map<std::string, int> usedTypes;
void CheckInstrs(const gd::Platform& pf, const gd::InstructionsList& list, bool isCond, const std::string& where) {
  for (std::size_t i = 0; i < list.size(); ++i) {
    const gd::Instruction& ins = list[i];
    auto type = ins.GetType();
    usedTypes[(isCond ? "C " : "A ") + type.ToLocale()]++;
    const auto& md = isCond ? gd::MetadataProvider::GetConditionMetadata(pf, type)
                            : gd::MetadataProvider::GetActionMetadata(pf, type);
    if (gd::MetadataProvider::IsBadInstructionMetadata(md)) {
      std::cout << "UNKNOWN " << (isCond ? "condition " : "action ") << type << " in " << where << "\n"; problems++;
    } else if (md.GetParametersCount() != ins.GetParametersCount()) {
      std::cout << "PARAMCOUNT " << type << " expected " << md.GetParametersCount() << " got " << ins.GetParametersCount() << " in " << where << "\n"; problems++;
    }
    CheckInstrs(pf, ins.GetSubInstructions(), isCond, where);
  }
}
void CheckEvents(const gd::Platform& pf, const gd::EventsList& evs, const std::string& where) {
  for (std::size_t i = 0; i < evs.size(); ++i) {
    const gd::BaseEvent& e = evs[i];
    usedTypes["E " + e.GetType().ToLocale()]++;
    if (e.GetType().empty() || e.GetType() == "BuiltinCommonInstructions::Empty") { std::cout << "EMPTY/UNKNOWN EVENT in " << where << "\n"; problems++; }
    for (auto* l : e.GetAllConditionsVectors()) CheckInstrs(pf, *l, true, where);
    for (auto* l : e.GetAllActionsVectors()) CheckInstrs(pf, *l, false, where);
    if (e.CanHaveSubEvents()) CheckEvents(pf, e.GetSubEvents(), where);
  }
}

int main(int argc, char** argv) {
  if (argc < 4) { std::cerr << "usage: gdexport game.json gdjsRoot outDir\n"; return 2; }
  auto& js = gdjs::JsPlatform::Get();
  for (auto lib : {"TextObject", "TiledSpriteObject"}) {
    std::string path = std::string("/tmp/gd/Binaries/Output/Release_Linux/CppPlatform/Extensions/") + lib + ".xgde";
    void* h = dlopen(path.c_str(), RTLD_NOW);
    if (!h) { std::cerr << dlerror() << "\n"; return 3; }
    auto create = (gd::PlatformExtension * (*)()) dlsym(h, "CreateGDJSExtension");
    js.AddExtension(std::shared_ptr<gd::PlatformExtension>(create()));
  }
  // Register platform (non-owning shared_ptr: singleton)
  gd::PlatformManager::Get()->AddPlatform(std::shared_ptr<gd::Platform>(&js, [](gd::Platform*) {}));

  std::ifstream in(argv[1]); std::stringstream ss; ss << in.rdbuf();
  gd::SerializerElement root = gd::Serializer::FromJSON(gd::String::FromUTF8(ss.str()));
  gd::Project project;
  project.UnserializeFrom(root);
  project.SetProjectFile(gd::String::FromUTF8(fs::absolute(argv[1]).string()));
  std::cout << "Loaded project: " << project.GetName() << " scenes=" << project.GetLayoutsCount()
            << " externalEvents=" << project.GetExternalEventsCount() << " externalLayouts=" << project.GetExternalLayoutsCount() << "\n";

  for (std::size_t i = 0; i < project.GetLayoutsCount(); ++i) {
    auto& l = project.GetLayout(i);
    std::cout << "  scene " << l.GetName() << ": objects=" << l.GetObjects().GetObjectsCount()
              << " instances=" << l.GetInitialInstances().GetInstancesCount() << " events=" << l.GetEvents().size() << "\n";
    CheckEvents(js, l.GetEvents(), "scene " + l.GetName().ToLocale());
  }
  for (std::size_t i = 0; i < project.GetExternalEventsCount(); ++i) {
    auto& e = project.GetExternalEvents(i);
    std::cout << "  external events " << e.GetName() << ": events=" << e.GetEvents().size() << "\n";
    CheckEvents(js, e.GetEvents(), "external " + e.GetName().ToLocale());
  }
  for (std::size_t i = 0; i < project.GetExternalLayoutsCount(); ++i) {
    auto& e = project.GetExternalLayout(i);
    std::cout << "  external layout " << e.GetName() << ": instances=" << e.GetInitialInstances().GetInstancesCount() << "\n";
  }
  std::cout << "Instruction/event types used:\n";
  for (auto& kv : usedTypes) std::cout << "    " << kv.first << " x" << kv.second << "\n";
  std::cout << "Instruction metadata problems: " << problems << "\n";

  NativeFS nfs;
  gdjs::Exporter exporter(nfs, argv[2]);
  exporter.SetCodeOutputDirectory("/tmp/gdexport_code");
  fs::remove_all("/tmp/gdexport_code"); fs::remove_all(argv[3]);
  gdjs::ExportOptions opts(project, argv[3]);
  bool ok = exporter.ExportWholePixiProject(opts);
  auto& report = project.GetWholeProjectDiagnosticReport();
  int diag = 0;
  for (std::size_t i = 0; i < report.Count(); ++i) {
    auto& r = report.Get(i);
    for (std::size_t j = 0; j < r.Count(); ++j) {
      auto& d = r.Get(j); diag++;
      std::cout << "DIAGNOSTIC [" << r.GetSceneName() << "] " << d.GetMessage() << " (object: " << d.GetObjectName()
                << ", actual: " << d.GetActualValue() << ", expected: " << d.GetExpectedValue() << ")\n";
    }
  }
  std::cout << "Export " << (ok ? "OK" : "FAILED: ") << exporter.GetLastError() << "  diagnostics=" << diag << "\n";
  return (ok && problems == 0 && diag == 0) ? 0 : 1;
}
