# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from flask import Flask, jsonify
from flask_restful import Resource, Api, reqparse
from . import guiltypatches
from libmozdata import config

app = Flask(__name__)
api = Api(app)


class Patches(Resource):

    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('channel', type=str, default='')
        parser.add_argument('product', type=str, default='')
        parser.add_argument('date', type=str, default='')
        args = parser.parse_args()
        output_dir = config.get('GuiltyPatches', 'output', None)

        if output_dir:
            if not (args.channel and args.product and args.date):
                return jsonify(guiltypatches.getdates(output_dir))
            else:
                return jsonify(guiltypatches.get(args.channel, args.product, args.date, output_dir))
        else:
            return jsonify({})


api.add_resource(Patches, '/patches', endpoint='patches')


if __name__ == '__main__':
    app.run()
