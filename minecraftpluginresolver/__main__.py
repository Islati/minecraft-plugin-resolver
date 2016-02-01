#!/usr/bin/python3
import sys
import minecraftpluginresolver
from minecraftpluginresolver import parser, MinecraftPluginResolver


def main(args=None):
    """The main entry point for the Minecraft Plugin Resolver."""
    if args is None:
        args = sys.argv[1:]

    args = parser.parse_args()
    minecraftpluginresolver.args = args
    app = MinecraftPluginResolver(args)
    app.run()


if __name__ == "__main__":
    main()
