// Copyright 2021 The Oppia Authors. All Rights Reserved.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS-IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

/**
 * @fileoverview Unit tests for Assign Skill To Topic Modal.
 */

import {ComponentFixture, TestBed, waitForAsync} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {NgbActiveModal} from '@ng-bootstrap/ng-bootstrap';
import {SelectTopicsComponent} from '../topic-selector/select-topics.component';
import {AssignSkillToTopicModalComponent} from './assign-skill-to-topic-modal.component';

describe('Assign Skill to Topic Modal Component', () => {
  let fixture: ComponentFixture<AssignSkillToTopicModalComponent>;
  let componentInstance: AssignSkillToTopicModalComponent;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      imports: [FormsModule],
      declarations: [AssignSkillToTopicModalComponent, SelectTopicsComponent],
      providers: [NgbActiveModal],
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(AssignSkillToTopicModalComponent);
    componentInstance = fixture.componentInstance;
    componentInstance.topicSummaries = [];
  });

  it('should create', () => {
    expect(componentInstance).toBeDefined();
  });
});
