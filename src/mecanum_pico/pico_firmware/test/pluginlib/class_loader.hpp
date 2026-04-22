// Minimal stub of pluginlib::ClassLoader for native unit tests
#pragma once

namespace pluginlib
{
template<typename T>
class ClassLoader
{
public:
  ClassLoader(const char * /*package*/, const char * /*base_class*/) {}
};
} // namespace pluginlib
