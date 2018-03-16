/**
 * Partials for the editor.
 */

import Config from '../utility/config'
import DeepObject from '../utility/deepObject'
import Defer from '../utility/defer'
import { fieldGenerator } from './field'

export default class Partials {
  constructor(api, config) {
    this.api = api
    this.config = new Config(config)

    this.deferredPartials = new Defer()
    this.api.getPartials().then(this.handleGetPartialsResponse.bind(this))
  }

  handleGetPartialsResponse(response) {
    this.deferredPartials.resolve(response['partials'])
  }
}

export class PartialContainer {
  constructor(key, label, frontMatter, fieldMeta, config) {
    // Create the field clone before setting any attributes.
    this.template = document.querySelector('#template_partial')
    this.fieldEl = document.importNode(this.template.content, true)
    this.labelEl = this.fieldEl.querySelector('.partial__label')
    this.fieldsEl = this.fieldEl.querySelector('.partial__fields')
    this.fields = []

    this.key = key
    this.label = label
    this.labelEl.innerText = `Partial: ${this.label}`
    this.frontMatter = new DeepObject(frontMatter)
    this.fieldMeta = fieldMeta
    this.config = new Config(config)

    for (const meta of this.fieldMeta) {
      const field = fieldGenerator(meta['type'], meta['key'], {}, this.partials)
      field.value = this.frontMatter.get(meta['key'])
      field.label = meta['label']
      this.fields.push(field)
      this.fieldsEl.appendChild(field.fieldEl)
    }
  }

  get value() {
    const value = {
      'partial': this.key,
    }

    for (const field of this.fields) {
      // Field key getter not working...?!?
      value[field._key] = field.value
    }

    return value
  }

  update(value) {
    // TODO: Figure out how to pass the updated data into the fields.
  }
}
